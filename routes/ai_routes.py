from fastapi import APIRouter, Depends, status
from controllers import ai_controller
from schemas import ChatRequest, ChatResponse, ContentGenerateRequest, ContentGenerateResponse, InsightRequest, InsightResponse
from utils.dependencies import require_onboarding_complete

router = APIRouter(prefix="/ai", tags=["AI"])

_onboarded = [Depends(require_onboarding_complete)]

router.add_api_route(
    "/chat",
    ai_controller.chat,
    methods=["POST"],
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    dependencies=_onboarded,
)

router.add_api_route(
    "/generate",
    ai_controller.generate_content,
    methods=["POST"],
    response_model=ContentGenerateResponse,
    status_code=status.HTTP_200_OK,
    dependencies=_onboarded,
)

router.add_api_route(
    "/insights",
    ai_controller.get_insights,
    methods=["POST"],
    response_model=InsightResponse,
    status_code=status.HTTP_200_OK,
    dependencies=_onboarded,
)

router.add_api_route(
    "/chat/history",
    ai_controller.get_chat_history,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
    dependencies=_onboarded,
)

router.add_api_route(
    "/providers",
    ai_controller.get_providers_status,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
)
