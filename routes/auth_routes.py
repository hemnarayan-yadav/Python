from fastapi import APIRouter, status
from controllers import auth_controller
from schemas import UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# Two endpoints, distinct paths -- otherwise FastAPI would only ever match
# the first one registered (same path + same method = unreachable second route).
router.add_api_route(
    "/register",
    auth_controller.register_user,
    methods=["POST"],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/login",
    auth_controller.login_user,
    methods=["POST"],
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)

