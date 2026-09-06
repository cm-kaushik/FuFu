from fastapi import APIRouter, Depends, HTTPException, status
import mysql.connector
from app.database.connection import get_db
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user, verify_pin
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse, BalanceUpdate

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, conn=Depends(get_db)):
    """Register a new user."""
    cursor = conn.cursor(dictionary=True)

    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username exists
    cursor.execute("SELECT id FROM users WHERE username = %s", (user_data.username,))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    password_hash = hash_password(user_data.password)
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, balance) VALUES (%s, %s, %s, %s)",
        (user_data.username, user_data.email, password_hash, 0.00)
    )
    conn.commit()
    user_id = cursor.lastrowid

    # Create token
    token = create_access_token({
        "user_id": user_id,
        "email": user_data.email,
        "username": user_data.username
    })

    cursor.close()

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            balance=0.00,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, conn=Depends(get_db)):
    """Login and get JWT token."""
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, username, email, password_hash, balance, created_at FROM users WHERE email = %s",
        (login_data.email,)
    )
    user = cursor.fetchone()
    cursor.close()

    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "user_id": user["id"],
        "email": user["email"],
        "username": user["username"]
    })

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            balance=float(user["balance"]),
            created_at=str(user["created_at"]) if user["created_at"] else None,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Get current user profile."""
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, email, balance, created_at FROM users WHERE id = %s",
        (current_user["user_id"],)
    )
    user = cursor.fetchone()
    cursor.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        balance=float(user["balance"]),
        created_at=str(user["created_at"]) if user["created_at"] else None,
    )


@router.post("/add-funds")
async def add_funds_endpoint(data: BalanceUpdate, current_user=Depends(get_current_user), conn=Depends(get_db)):
    """Add virtual funds to account (requires PIN 2468)."""
    from app.services.trading_service import add_funds
    result = add_funds(conn, current_user["user_id"], data.amount, data.pin)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result
