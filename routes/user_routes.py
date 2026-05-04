from typing import List
from fastapi import APIRouter, Depends, status

from controllers import user_controllers
from schemas import UserResponse
from utils.dependencies import get_current_user


# APIRouter = a mini FastAPI app you can mount under a prefix.
# prefix="/users" -> every route below is automatically /users/...
# tags=["Users"]  -> groups them in the auto-generated /docs UI.
# dependencies=[Depends(get_current_user)] applies JWT auth to EVERY route
# in this router -- acts like a middleware. Requests without a valid Bearer
# token get a 401 before the controller ever runs.
router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(get_current_user)])


# We register the controller functions DIRECTLY as the route handlers.
# This way FastAPI sees their real type hints (UserCreate, Session, etc.)
# and can wire validation, dependency injection and OpenAPI docs correctly.
#
# Equivalent decorator form would be:
#     @router.post("/", response_model=UserResponse, status_code=201)
#     def create_user(user: UserCreate, db: Session = Depends(get_db)): ...
# but since the controller already has that exact signature, we just point
# the route at it.

router.add_api_route(
    "/",
    user_controllers.create_user,
    methods=["POST"],
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)

router.add_api_route(
    "/",
    user_controllers.list_users,
    methods=["GET"],
    response_model=List[UserResponse],
)

router.add_api_route(
    "/{user_id}",
    user_controllers.get_user,
    methods=["GET"],
    response_model=UserResponse,
)

router.add_api_route(
    "/{user_id}",
    user_controllers.update_user,
    methods=["PATCH"],
    response_model=UserResponse,
)

router.add_api_route(
    "/{user_id}",
    user_controllers.delete_user,
    methods=["DELETE"],
)