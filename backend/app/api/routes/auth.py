from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenResponse
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    PasswordResetMessage,
    ResetPasswordRequest,
)
from app.schemas.user import (
    UserCreate,
    UserPasswordUpdate,
    UserProfileUpdate,
    UserResponse,
)
from app.security.dependencies import get_current_user
from app.security.password import hash_password, verify_password
from app.services.auth_service import authenticate_user
from app.services.email_service import send_password_reset_email
from app.services.password_reset_service import (
    create_password_reset_token,
    reset_user_password,
)
from app.services.user_service import register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    return register_user(
        db=db,
        user_data=user_data,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    _, access_token, expires_in = authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user

@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    normalized_name = profile_data.full_name.strip()

    if len(normalized_name) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El nombre debe tener al menos 3 caracteres.",
        )

    current_user.full_name = normalized_name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.patch(
    "/change-password",
    status_code=status.HTTP_200_OK,
)
def change_current_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta.",
        )

    if verify_password(
        password_data.new_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "La nueva contraseña debe ser diferente "
                "de la contraseña actual."
            ),
        )

    current_user.password_hash = hash_password(
        password_data.new_password
    )

    current_user.failed_login_attempts = 0
    current_user.locked_until = None

    db.add(current_user)
    db.commit()

    return {
        "message": (
            "Contraseña actualizada correctamente. "
            "Inicia sesión nuevamente."
        )
    }

@router.post(
    "/forgot-password",
    response_model=PasswordResetMessage,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PasswordResetMessage:
    generic_message = (
        "Si el correo está registrado, recibirás instrucciones "
        "para restablecer tu contraseña."
    )

    normalized_email = request_data.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if user is None or not user.is_active:
        return PasswordResetMessage(
            message=generic_message
        )

    plain_token = create_password_reset_token(
        db=db,
        user=user,
    )

    reset_url = (
        f"{settings.frontend_url}"
        f"/?reset_token={plain_token}"
    )

    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.full_name,
        reset_url,
    )

    return PasswordResetMessage(
        message=generic_message
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetMessage,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> PasswordResetMessage:
    reset_user_password(
        db=db,
        plain_token=request_data.token,
        new_password=request_data.new_password,
    )

    return PasswordResetMessage(
        message=(
            "Contraseña actualizada correctamente. "
            "Ya puedes iniciar sesión."
        )
    )