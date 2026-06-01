from fastapi import APIRouter, status
from controllers import auth_controller
from schemas import TokenResponse, RegisterResponse, AuthUserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

router.add_api_route(
    "/register",
    auth_controller.register_user,
    methods=["POST"],
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/login",
    auth_controller.login_user,
    methods=["POST"],
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)

router.add_api_route(
    "/me",
    auth_controller.get_current_user_profile,
    methods=["GET"],
    response_model=AuthUserResponse,
    status_code=status.HTTP_200_OK,
)
