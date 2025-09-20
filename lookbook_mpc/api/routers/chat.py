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
from datetime import datetime

from ...domain.entities import ChatRequest, ChatResponse
from ...domain.use_cases import ChatTurn
from ...adapters.intent import MockIntentParser
from ...adapters.db_lookbook import MockLookbookRepository
from ...services.rules import RulesEngine
from ...services.recommender import OutfitRecommender

router = APIRouter(prefix="/v1/chat", tags=["chat"])
logger = structlog.get_logger()


# Initialize dependencies (will be replaced with proper DI in later milestones)
intent_parser = MockIntentParser()
lookbook_repo = MockLookbookRepository()
rules_engine = RulesEngine()
recommender = OutfitRecommender(rules_engine)
chat_use_case = ChatTurn(intent_parser, recommender, lookbook_repo)


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
    try:
        logger.info("Processing chat turn",
                   session_id=request.session_id,
                   message=request.message)

        # Execute chat use case
        response = await chat_use_case.execute(request)

        # Generate session ID if not provided
        if not response.session_id:
            response.session_id = str(uuid.uuid4())

        # Initialize session if new
        if response.session_id not in sessions:
            sessions[response.session_id] = {
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {}
            }

        # Add message to session history
        sessions[response.session_id]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "content": request.message
        })

        # Add assistant response to session history
        sessions[response.session_id]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": response.replies[0]["message"] if response.replies else "I'm here to help!"
        })

        # Update session context with recommendations
        if response.outfits:
            sessions[response.session_id]["context"]["last_recommendations"] = response.outfits

        logger.info("Chat turn completed",
                   session_id=response.session_id,
                   replies_count=len(response.replies),
                   has_outfits=bool(response.outfits))

        return response

    except ValueError as e:
        logger.error("Validation error in chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Chat processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip")
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
            sessions_list.append({
                "session_id": session_id,
                "created_at": session_data["created_at"],
                "message_count": len(session_data["messages"]),
                "has_recommendations": bool(session_data["context"].get("last_recommendations"))
            })

        # Sort by creation time (newest first)
        sessions_list.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_sessions = sessions_list[offset:offset + limit]

        return {
            "sessions": paginated_sessions,
            "pagination": {
                "total": len(sessions_list),
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < len(sessions_list)
            }
        }

    except Exception as e:
        logger.error("Error listing sessions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
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
                detail=f"Session {session_id} not found"
            )

        session_data = sessions[session_id]

        return {
            "session_id": session_id,
            "created_at": session_data["created_at"],
            "messages": session_data["messages"],
            "context": session_data["context"],
            "message_count": len(session_data["messages"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
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
                detail=f"Session {session_id} not found"
            )

        # Delete session
        del sessions[session_id]

        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "deleted_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
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
                    "description": "Find comfortable yoga outfits"
                },
                {
                    "id": "dinner_date",
                    "prompt": "Restaurant this weekend, attractive for $50",
                    "category": "occasion",
                    "description": "Get dinner outfit recommendations within budget"
                },
                {
                    "id": "slimming_look",
                    "prompt": "I am fat, look slim",
                    "category": "objective",
                    "description": "Find slimming outfit options"
                },
                {
                    "id": "casual_everyday",
                    "prompt": "I need casual everyday outfits",
                    "category": "style",
                    "description": "Get casual style recommendations"
                },
                {
                    "id": "business_meeting",
                    "prompt": "Business meeting outfit for tomorrow",
                    "category": "occasion",
                    "description": "Professional business outfit suggestions"
                },
                {
                    "id": "party_look",
                    "prompt": "Party outfit for Saturday night",
                    "category": "occasion",
                    "description": "Stylish party outfit recommendations"
                },
                {
                    "id": "beach_vacation",
                    "prompt": "Beach vacation outfits",
                    "category": "occasion",
                    "description": "Comfortable beach and vacation wear"
                },
                {
                    "id": "sport_workout",
                    "prompt": "Sport workout clothes",
                    "category": "activity",
                    "description": "Athletic workout gear recommendations"
                }
            ],
            "categories": ["activity", "occasion", "objective", "style"]
        }

        return suggestions_response

    except Exception as e:
        logger.error("Error getting chat suggestions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
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
                detail=f"Session {session_id} not found"
            )

        # Clear context but keep messages
        sessions[session_id]["context"] = {}
        sessions[session_id]["context_cleared_at"] = datetime.now().isoformat()

        return {
            "message": "Session context cleared successfully",
            "session_id": session_id,
            "cleared_at": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error clearing session context", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session context: {str(e)}"
        )