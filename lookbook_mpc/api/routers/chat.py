"""
Chat API Router

This module handles endpoints for chat-based fashion recommendations
and conversational interactions.
"""

from fastapi import APIRouter, HTTPException, status, Query, Request
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
async def chat_turn(request: ChatRequest, request_obj: Request = None) -> ChatResponse:
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

        # Calculate recommendation time (approximate)
        recommendation_time_ms = None
        if response.outfits and len(response.outfits) > 0:
            # Estimate recommendation time as response time minus intent parsing time
            recommendation_time_ms = max(0, response_time_ms - intent_time)

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

        # Parse intent for logging (reuse the intent parsing that happened in the use case)
        parsed_intent = None
        intent_confidence = None
        language_detected = None
        try:
            # Get intent parsing results - we need to re-parse since the use case doesn't return it
            intent_result = await intent_parser.parse_intent(request.message)
            parsed_intent = intent_result  # It's already a dict
            # For now, set a default confidence since the parser doesn't provide it
            intent_confidence = 0.8  # Default confidence for LLM-based parsing
            # Extract language if available from intent result
            language_detected = intent_result.get("language") or intent_result.get("detected_language")
        except Exception as e:
            logger.warning(f"Failed to parse intent for logging: {e}")

        # Extract request metadata
        user_ip = None
        user_agent = None
        if request_obj:
            # Get client IP (handle forwarded headers)
            user_ip = (
                request_obj.headers.get("x-forwarded-for") or
                request_obj.headers.get("x-real-ip") or
                getattr(request_obj.client, 'host', None) if request_obj.client else None
            )
            if user_ip and "," in user_ip:
                user_ip = user_ip.split(",")[0].strip()  # Take first IP if multiple

            user_agent = request_obj.headers.get("user-agent")

        # Determine more accurate response type
        ai_response_type = "general"
        if response.replies and len(response.replies) > 0:
            reply_type = response.replies[0].get("type", "assistant")
            if reply_type == "recommendations" or (response.outfits and len(response.outfits) > 0):
                ai_response_type = "recommendations"
            elif reply_type == "error":
                ai_response_type = "error"
            elif reply_type == "clarification":
                ai_response_type = "clarification"
            else:
                ai_response_type = "assistant"

        # Create log entry with improved accuracy
        log_entry = ChatLogEntry(
            session_id=response.session_id,
            request_id=response.request_id,
            user_message=request.message,
            ai_response=response.replies[0]["message"] if response.replies else None,
            ai_response_type=ai_response_type,
            parsed_intent=parsed_intent,
            intent_confidence=intent_confidence,
            intent_parser_type="llm",  # More accurate than "hybrid"
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
            recommendation_time_ms=recommendation_time_ms,
            user_ip=user_ip,
            user_agent=user_agent,
            language_detected=language_detected,
            conversation_turn_number=session_context["next_turn_number"],
            previous_message_id=None,  # Could be implemented with message threading
            is_follow_up=session_context["total_messages"] > 0,
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
            log_entry.error_stack_trace = None  # Could add traceback.format_exc() if needed
            log_entry.response_time_ms = int((time.time() - start_time) * 1000)
            log_entry.user_ip = user_ip if 'user_ip' in locals() else None
            log_entry.user_agent = user_agent if 'user_agent' in locals() else None
            chat_logger.log_chat_interaction(log_entry)

        logger.error("Validation error in chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        # Log error interaction
        if request.session_id or hasattr(request, "session_id"):
            import traceback
            error_log_entry = ChatLogEntry(
                session_id=request.session_id or str(uuid.uuid4()),
                request_id=str(uuid.uuid4()),
                user_message=request.message,
                ai_response="I apologize, but I encountered an error processing your request.",
                ai_response_type="error",
                parsed_intent=parsed_intent if 'parsed_intent' in locals() else None,
                intent_confidence=intent_confidence if 'intent_confidence' in locals() else None,
                intent_parser_type="llm",
                strategy_config={
                    "name": strategy.name if 'strategy' in locals() else "unknown",
                    "tone": strategy.tone if 'strategy' in locals() else "neutral",
                },
                error_occurred=True,
                error_message=str(e),
                error_stack_trace=traceback.format_exc(),
                response_time_ms=int((time.time() - start_time) * 1000),
                intent_parsing_time_ms=intent_time if 'intent_time' in locals() else None,
                user_ip=user_ip if 'user_ip' in locals() else None,
                user_agent=user_agent if 'user_agent' in locals() else None,
                language_detected=language_detected if 'language_detected' in locals() else None,
                conversation_turn_number=session_context.get("next_turn_number", 1) if 'session_context' in locals() else 1,
                is_follow_up=session_context.get("total_messages", 0) > 0 if 'session_context' in locals() else False,
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
    List chat sessions from database.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of chat sessions with latest message info
    """
    try:
        logger.info("Listing chat sessions", limit=limit, offset=offset)

        # Get sessions from database
        connection = chat_logger._get_db_connection()
        with connection.cursor() as cursor:
            # Get total count for pagination
            cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE is_active = 1")
            total_count = cursor.fetchone()[0]

            # Get sessions with latest message info
            cursor.execute(
                """
                SELECT
                    cs.session_id,
                    cs.name,
                    cs.created_at,
                    cs.last_activity,
                    cs.total_messages,
                    cs.total_recommendations,
                    cl.user_message as last_user_message,
                    cl.ai_response as last_ai_message,
                    cl.created_at as last_message_time
                FROM chat_sessions cs
                LEFT JOIN chat_logs cl ON cs.session_id = cl.session_id
                    AND cl.created_at = (
                        SELECT MAX(created_at)
                        FROM chat_logs cl2
                        WHERE cl2.session_id = cs.session_id
                    )
                WHERE cs.is_active = 1
                ORDER BY cs.last_activity DESC
                LIMIT %s OFFSET %s
            """,
                (limit, offset),
            )

            results = cursor.fetchall()

        connection.close()

        # Format sessions data
        sessions_list = []
        for row in results:
            (
                session_id,
                session_name,
                created_at,
                last_activity,
                total_messages,
                total_recommendations,
                last_user_msg,
                last_ai_msg,
                last_msg_time,
            ) = row

            # Determine last message to display
            last_message = (
                last_ai_msg
                if last_ai_msg
                else last_user_msg
                if last_user_msg
                else "No messages yet"
            )
            if last_message and len(last_message) > 60:
                last_message = last_message[:60] + "..."

            sessions_list.append(
                {
                    "session_id": session_id,
                    "name": session_name or f"Customer {session_id[:8]}...",  # Use stored name or generate display name
                    "avatar": f"/assets/images/avatar_{hash(session_id) % 9 + 1}.webp",  # Consistent avatar
                    "created_at": created_at.isoformat() if created_at else None,
                    "last_activity": last_activity.isoformat()
                    if last_activity
                    else None,
                    "total_messages": total_messages or 0,
                    "total_recommendations": total_recommendations or 0,
                    "last_message": last_message,
                    "timestamp": last_msg_time.strftime("%H:%M")
                    if last_msg_time
                    else "",
                    "status": "online",  # Default status
                    "has_recommendations": (total_recommendations or 0) > 0,
                }
            )

        return {
            "sessions": sessions_list,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count,
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
    Delete a chat session and all its logs.

    Args:
        session_id: ID of the session to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If session is not found or deletion fails
    """
    try:
        logger.info("Deleting session", session_id=session_id)

        connection = chat_logger._get_db_connection()
        with connection.cursor() as cursor:
            # Delete chat logs first
            cursor.execute("DELETE FROM chat_logs WHERE session_id = %s", (session_id,))

            # Delete session
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))

            deleted_logs = cursor.rowcount

        connection.commit()
        connection.close()

        if deleted_logs == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found",
            )

        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "logs_deleted": deleted_logs,
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


@router.post("/sessions/{session_id}/generate-title")
async def generate_session_title(session_id: str) -> Dict[str, Any]:
    """
    Generate an AI-powered title for a chat session.

    Args:
        session_id: ID of the session to generate title for

    Returns:
        Generated title for the session
    """
    try:
        logger.info("Generating AI title for session", session_id=session_id)

        # Get conversation history
        history = chat_logger.get_conversation_history(session_id, limit=10)

        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No conversation history found for session {session_id}",
            )

        # Prepare conversation text for AI
        conversation_text = ""
        for msg in history:
            if msg.get("user_message"):
                conversation_text += f"User: {msg['user_message']}\n"
            if msg.get("ai_response"):
                conversation_text += f"AI: {msg['ai_response']}\n"

        # Create prompt for title generation
        prompt = f"""Based on this conversation, generate a concise, descriptive title (max 50 characters) that captures the main topic or intent:

{conversation_text}

Title:"""

        # Use Ollama to generate title
        response = ollama_provider.generate_text(
            prompt=prompt,
            max_tokens=50,
            temperature=0.7
        )

        title = response.strip().strip('"').strip("'")[:50]  # Clean and limit length

        # Update session name in database
        connection = chat_logger._get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chat_sessions
                SET name = %s
                WHERE session_id = %s
                """,
                (title, session_id),
            )

        connection.commit()
        connection.close()

        logger.info("Generated title for session", session_id=session_id, title=title)

        return {
            "session_id": session_id,
            "title": title,
            "generated_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error generating session title", session_id=session_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate title: {str(e)}",
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
