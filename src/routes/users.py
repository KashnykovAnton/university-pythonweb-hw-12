from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status,
    BackgroundTasks,
    UploadFile,
    File,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.database.db import get_db
from src.schemas.user import UserResponse
from src.services.auth import AuthService, oauth2_scheme
from src.entity.models import User
from src.core.depend_service import (
    get_auth_service,
    get_current_moderator_user,
    get_current_admin_user,
    get_current_user,
    get_user_service,
)
from src.conf import messages
from src.services.email import send_email
from src.schemas.email import RequestEmail
from src.services.user import UserService
from src.core.depend_service import get_user_service
from src.core.email_token import get_email_from_token
from src.services.upload_file_service import UploadFileService
from src.conf.config import settings


router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
    email = get_email_from_token(token)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": messages.email_already_confirmed.get("ua")}
    await user_service.confirmed_email(email)
    return {"message": messages.email_confirmed.get("ua")}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_user_by_email(str(body.email))

    if user.confirmed:
        return {"message": messages.email_already_confirmed.get("ua")}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": messages.email_confirm_request.get("ua")}


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME, settings.CLOUDINARY_API_KEY, settings.CLOUDINARY_API_SECRET
    ).upload_file(file, user.username)

    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user


@router.get("/moderator")
def read_moderator(
    current_user: User = Depends(get_current_moderator_user),
):
    return {
        "message": messages.welcome_messages["moderator"]
        .get("ua")
        .format(username=current_user.username)
    }


@router.get("/admin")
def read_admin(current_user: User = Depends(get_current_admin_user)):
    return {
        "message": messages.welcome_messages["admin"]
        .get("ua")
        .format(username=current_user.username)
    }
