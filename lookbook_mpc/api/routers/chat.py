"""
Chat API Router

This module handles endpoints for chat-based fashion recommendations
and conversational interactions.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
import structlog
import uuid
import time
from datetime import datetime

from ...domain.entities import ChatRequest, ChatResponse
from ...domain.use_cases import ChatTurn
from ...adapters.intent import LLMIntentParser
from ...adapters.db_lookbook import MySQLLookbookRepository
from ...services.rules import RulesEngine
from ...services.recommender import OutfitRecommender
from ...services.strategy import StrategyService
from ...services.chat_logger import ChatLogger, ChatLogEntry
from ...config import settings

router = APIRouter(prefix="/v1/chat", tags=["chat"])
logger = structlog.get_logger()


# Initialize dependencies (will be replaced with proper DI in later milestones)
from lookbook_mpc.adapters.llm_providers import OllamaProvider

ollama_provider = OllamaProvider(
    host=settings.ollama_host,
    model=settings.ollama_text_model_fast,  # Use fast model for better performance
    timeout=10,  # Shorter timeout for faster model
)
intent_parser = LLMIntentParser(provider=ollama_provider)
lookbook_repo = MySQLLookbookRepository(settings.lookbook_db_url)
rules_engine = RulesEngine()
recommender = OutfitRecommender(rules_engine)
chat_use_case = ChatTurn(intent_parser, recommender, lookbook_repo)
strategy_service = StrategyService()
chat_logger = ChatLogger()


# In-memory session storage (in production, use Redis or database)
sessions: Dict[str, Dict[str, Any]] = {}


@router.post("", response_model=ChatResponse)
async def chat_turn(request: ChatRequest) -> ChatResponse:
    """
    Process a chat turn for fashion recommendations.

    This endpoint handles conversational interactions for fashion
    recommendations, understanding user intent and providing
    appropriate responses with outfit suggestions.

    Args:
        request: Chat request with session and message

    Returns:
        ChatResponse with replies and optional outfit recommendations

    Raises:
        HTTPException: If chat processing fails
    """
    start_time = time.time()
    response_time_ms = None
    log_entry = None

    try:
        logger.info(
            "Processing chat turn",
            session_id=request.session_id,
            message=request.message,
        )

        # Get session context for conversation flow
        session_context = chat_logger.get_session_context(request.session_id or "")

        # Get strategy for this session
        strategy_override = (
            getattr(request, "meta", {}).get("strategy_override")
            if hasattr(request, "meta")
            else None
        )
        strategy = strategy_service.get_strategy(
            request.session_id or "", strategy_override
        )

        # Build system directive from strategy
        system_directive = strategy_service.build_system_directive(strategy)

        # Add strategy context to request (extend ChatRequest if needed)
        # For now, we'll pass it through the use case

        # Execute chat use case with timing
        intent_start = time.time()
        response = await chat_use_case.execute(request)
        intent_time = int((time.time() - intent_start) * 1000)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Generate session ID if not provided
        if not response.session_id:
            response.session_id = str(uuid.uuid4())

        # Apply tone post-processing to response
        if response.replies and len(response.replies) > 0:
            original_message = response.replies[0].get("message", "")
            toned_message = strategy_service.apply_reply_tone(
                original_message, strategy
            )
            response.replies[0]["message"] = toned_message

        # Create log entry
        log_entry = ChatLogEntry(
            session_id=response.session_id,
            request_id=response.request_id,
            user_message=request.message,
            ai_response=response.replies[0]["message"] if response.replies else None,
            ai_response_type=response.replies[0].get("type", "general")
            if response.replies
            else "general",
            strategy_config={
                "name": strategy.name,
                "tone": strategy.tone,
                "language": strategy.language,
                "objectives": strategy.objectives,
                "guardrails": strategy.guardrails,
                "style_config": strategy.style_config,
            },
            tone_applied=strategy.tone,
            system_directive=system_directive,
            outfits_count=len(response.outfits) if response.outfits else 0,
            outfits_data=response.outfits if response.outfits else None,
            response_time_ms=response_time_ms,
            intent_parsing_time_ms=intent_time,
            conversation_turn_number=session_context["next_turn_number"],
            is_follow_up=session_context["total_messages"] > 0,
            intent_parser_type="hybrid",
        )

        # Initialize session if new (maintain backward compatibility)
        if response.session_id not in sessions:
            sessions[response.session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {},
            }

        # Add message to session history (backward compatibility)
        sessions[response.session_id]["messages"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "role": "user",
                "content": request.message,
            }
        )

        sessions[response.session_id]["messages"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response.replies[0]["message"]
                if response.replies
                else "I'm here to help!",
            }
        )

        # Update session context with recommendations
        if response.outfits:
            sessions[response.session_id]["context"]["last_recommendations"] = (
                response.outfits
            )

        # Log to database
        chat_logger.log_chat_interaction(log_entry)

        logger.info(
            "Chat turn completed",
            session_id=response.session_id,
            replies_count=len(response.replies),
            has_outfits=bool(response.outfits),
            response_time_ms=response_time_ms,
            strategy_used=strategy.name,
        )

        return response

    except ValueError as e:
        # Log error interaction
        if log_entry:
            log_entry.error_occurred = True
            log_entry.error_message = str(e)
            log_entry.response_time_ms = int((time.time() - start_time) * 1000)
            chat_logger.log_chat_interaction(log_entry)

        logger.error("Validation error in chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        # Log error interaction
        if request.session_id or hasattr(request, "session_id"):
            error_log_entry = ChatLogEntry(
                session_id=request.session_id or str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                user_message=request.message,
                ai_response="I apologize, but I encountered an error processing your request.",
                ai_response_type="error",
                error_occurred=True,
                error_message=str(e),
                response_time_ms=int((time.time() - start_time) * 1000),
                intent_parser_type="hybrid",
            )
            chat_logger.log_chat_interaction(error_log_entry)

        logger.error("Chat processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of sessions to return"
    ),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
) -> Dict[str, Any]:
    """
    List chat sessions.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of chat sessions
    """
    try:
        logger.info("Listing chat sessions", limit=limit, offset=offset)

        # Convert sessions dict to list for pagination
        sessions_list = []
        for session_id, session_data in sessions.items():
            sessions_list.append(
                {
                    "session_id": session_id,
                    "created_at": session_data["created_at"],
                    "message_count": len(session_data["messages"]),
                    "has_recommendations": bool(
                        session_data["context"].get("last_recommendations")
                    ),
                }
            )

        # Sort by creation time (newest first)
        sessions_list.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_sessions = sessions_list[offset : offset + limit]

        return {
            "sessions": paginated_sessions,
            "pagination": {
                "total": len(sessions_list),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(sessions_list),
            },
        }

    except Exception as e:
        logger.error("Error listing sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}",
        )


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Get details of a specific chat session.

    Args:
        session_id: ID of the session to retrieve

    Returns:
        Session details including message history

    Raises:
        HTTPException: If session is not found
    """
    try:
        logger.info("Getting session details", session_id=session_id)

        if session_id not in sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        session_data = sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "messages": session_data["messages"],
            "context": session_data["context"],
            "message_count": len(session_data["messages"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}",
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """
    Delete a chat session.

    Args:
        session_id: ID of the session to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If session is not found or deletion fails
    """
    try:
        logger.info("Deleting session", session_id=session_id)

        if session_id not in sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Delete session
        del sessions[session_id]

        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "deleted_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        )


@router.get("/suggestions")
async def get_chat_suggestions() -> Dict[str, Any]:
    """
    Get suggested chat prompts for users.

    Returns:
        List of suggested chat prompts
    """
    try:
        logger.info("Getting chat suggestions")

        suggestions_response = {
            "suggestions": [
                {
                    "id": "yoga_outfit",
                    "prompt": "I want to do yoga",
                    "category": "activity",
                    "description": "Find comfortable yoga outfits",
                },
                {
                    "id": "dinner_date",
                    "prompt": "Restaurant this weekend, attractive for $50",
                    "category": "occasion",
                    "description": "Get dinner outfit recommendations within budget",
                },
                {
                    "id": "slimming_look",
                    "prompt": "I am fat, look slim",
                    "category": "objective",
                    "description": "Find slimming outfit options",
                },
                {
                    "id": "casual_everyday",
                    "prompt": "I need casual everyday outfits",
                    "category": "style",
                    "description": "Get casual style recommendations",
                },
                {
                    "id": "business_meeting",
                    "prompt": "Business meeting outfit for tomorrow",
                    "category": "occasion",
                    "description": "Professional business outfit suggestions",
                },
                {
                    "id": "party_look",
                    "prompt": "Party outfit for Saturday night",
                    "category": "occasion",
                    "description": "Stylish party outfit recommendations",
                },
                {
                    "id": "beach_vacation",
                    "prompt": "Beach vacation outfits",
                    "category": "occasion",
                    "description": "Comfortable beach and vacation wear",
                },
                {
                    "id": "sport_workout",
                    "prompt": "Sport workout clothes",
                    "category": "activity",
                    "description": "Athletic workout gear recommendations",
                },
            ],
            "categories": ["activity", "occasion", "objective", "style"],
        }

        return suggestions_response

    except Exception as e:
        logger.error("Error getting chat suggestions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}",
        )


@router.post("/sessions/{session_id}/clear")
async def clear_session_context(session_id: str) -> Dict[str, Any]:
    """
    Clear the context of a chat session.

    Args:
        session_id: ID of the session to clear

    Returns:
        Context cleared confirmation

    Raises:
        HTTPException: If session is not found
    """
    try:
        logger.info("Clearing session context", session_id=session_id)

        if session_id not in sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        # Clear context but keep messages
        sessions[session_id]["context"] = {}
        sessions[session_id]["context_cleared_at"] = datetime.now().isoformat()

        return {
            "message": "Session context cleared successfully",
            "session_id": session_id,
            "cleared_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error clearing session context", session_id=session_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session context: {str(e)}",
        )


@router.post("/sessions/{session_id}/strategy")
async def set_session_strategy(
    session_id: str, strategy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Set strategy for a specific session.

    Args:
        session_id: ID of the session
        strategy: Strategy configuration

    Returns:
        Strategy confirmation
    """
    try:
        logger.info(
            "Setting session strategy", session_id=session_id, strategy=strategy
        )

        success = strategy_service.set_session_strategy(
            session_id, strategy.get("name", "default")
        )

        if success:
            return {
                "message": "Strategy set successfully",
                "session_id": session_id,
                "strategy": strategy,
                "updated_at": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid strategy name or configuration",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error setting session strategy", session_id=session_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set session strategy: {str(e)}",
        )


@router.get("/strategy-presets")
async def get_strategy_presets() -> Dict[str, Any]:
    """
    Get available strategy presets.

    Returns:
        List of available strategies
    """
    try:
        logger.info("Getting strategy presets")

        strategies = strategy_service.get_available_strategies()

        return {"strategies": strategies, "total": len(strategies)}

    except Exception as e:
        logger.error("Error getting strategy presets", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy presets: {str(e)}",
        )


@router.get("/sessions/{session_id}/logs")
async def get_session_logs(
    session_id: str, limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get conversation logs for a session.

    Args:
        session_id: Session identifier
        limit: Maximum number of messages to return

    Returns:
        Conversation history
    """
    try:
        logger.info("Getting session logs", session_id=session_id, limit=limit)

        history = chat_logger.get_conversation_history(session_id, limit)

        return {
            "session_id": session_id,
            "conversation_history": history,
            "total_messages": len(history),
        }

    except Exception as e:
        logger.error("Error getting session logs", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session logs: {str(e)}",
        )


@router.get("/performance")
async def get_chat_performance(days: int = Query(7, ge=1, le=30)) -> Dict[str, Any]:
    """
    Get chat system performance metrics.

    Args:
        days: Number of days to analyze

    Returns:
        Performance metrics
    """
    try:
        logger.info("Getting chat performance metrics", days=days)

        metrics = chat_logger.get_performance_metrics(days)

        return {
            "performance_metrics": metrics,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error("Error getting performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}",
        )
