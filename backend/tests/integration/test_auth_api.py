"""Authentication API 整合測試"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from jose import jwt
from app.config import settings


class TestRegisterAPI:
    """註冊 API 測試"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """測試註冊成功"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # 不應該返回密碼

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """測試 Email 重複"""
        # 第一次註冊
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "password123"
            }
        )

        # 第二次使用相同 email 註冊
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """測試 Username 重複"""
        # 第一次註冊
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "username": "sameusername",
                "password": "password123"
            }
        )

        # 第二次使用相同 username 註冊
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "username": "sameusername",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email_format(self, client: AsyncClient):
        """測試 Email 格式錯誤"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Pydantic validation error


class TestLoginAPI:
    """登入 API 測試"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """測試登入成功，返回 token"""
        # 先註冊用戶
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "loginuser@example.com",
                "username": "loginuser",
                "password": "password123"
            }
        )

        # 登入
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

        # 驗證 token 可以解碼
        token = data["access_token"]
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["email"] == "loginuser@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """測試密碼錯誤"""
        # 先註冊用戶
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "testuser",
                "password": "correctpassword"
            }
        )

        # 使用錯誤密碼登入
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client: AsyncClient):
        """測試用戶不存在"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]


class TestGetCurrentUserAPI:
    """取得當前用戶 API 測試"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_client: AsyncClient, test_user):
        """測試 GET /auth/me 成功"""
        response = await auth_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """測試無 token"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """測試無效 token"""
        client.headers["Authorization"] = "Bearer invalid.token.here"
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, client: AsyncClient):
        """測試過期 token"""
        # 建立已過期的 token
        expire = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        client.headers["Authorization"] = f"Bearer {expired_token}"
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_malformed_token(self, client: AsyncClient):
        """測試格式錯誤的 token"""
        client.headers["Authorization"] = "NotBearer token123"
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
