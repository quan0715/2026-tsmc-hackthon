"""Authentication Service 單元測試"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.services.auth_service import AuthService
from app.config import settings


class TestPasswordHashing:
    """密碼加密測試"""

    @pytest.mark.asyncio
    async def test_hash_password(self, auth_service: AuthService):
        """測試密碼加密"""
        password = "mySecurePassword123"
        hashed = auth_service.hash_password(password)

        # 確保 hash 不等於原始密碼
        assert hashed != password
        # 確保 hash 是 bcrypt 格式 (以 $2b$ 開頭)
        assert hashed.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_verify_password_correct(self, auth_service: AuthService):
        """測試正確密碼驗證"""
        password = "mySecurePassword123"
        hashed = auth_service.hash_password(password)

        # 正確密碼應該驗證成功
        assert auth_service.verify_password(password, hashed) is True

    @pytest.mark.asyncio
    async def test_verify_password_incorrect(self, auth_service: AuthService):
        """測試錯誤密碼驗證"""
        password = "mySecurePassword123"
        wrong_password = "wrongPassword456"
        hashed = auth_service.hash_password(password)

        # 錯誤密碼應該驗證失敗
        assert auth_service.verify_password(wrong_password, hashed) is False


class TestJWTToken:
    """JWT Token 測試"""

    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service: AuthService):
        """測試 JWT token 生成"""
        user_id = "user123"
        email = "user@example.com"

        token, expires_in = auth_service.create_access_token(user_id, email)

        # 確保 token 是字串
        assert isinstance(token, str)
        assert len(token) > 0

        # 確保過期時間正確
        expected_expires = settings.jwt_access_token_expire_hours * 3600
        assert expires_in == expected_expires

        # 解碼並驗證 payload
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_decode_token_valid(self, auth_service: AuthService):
        """測試有效 token 解碼"""
        user_id = "user123"
        email = "user@example.com"
        token, _ = auth_service.create_access_token(user_id, email)

        payload = auth_service.decode_token(token)

        assert payload["sub"] == user_id
        assert payload["email"] == email

    @pytest.mark.asyncio
    async def test_decode_token_expired(self, auth_service: AuthService):
        """測試過期 token 處理"""
        # 建立已過期的 token
        expire = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        # 解碼過期 token 應該拋出 ValueError
        with pytest.raises(ValueError, match="Invalid token"):
            auth_service.decode_token(token)

    @pytest.mark.asyncio
    async def test_decode_token_invalid(self, auth_service: AuthService):
        """測試無效 token 處理"""
        invalid_token = "this.is.not.a.valid.token"

        with pytest.raises(ValueError, match="Invalid token"):
            auth_service.decode_token(invalid_token)


class TestCreateUser:
    """建立用戶測試"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, auth_service: AuthService):
        """測試成功建立用戶"""
        email = "newuser@example.com"
        username = "newuser"
        password = "password123"

        user = await auth_service.create_user(email, username, password)

        assert user.email == email
        assert user.username == username
        assert user.is_active is True
        assert user.password_hash != password  # 密碼已加密
        assert user.password_hash.startswith("$2b$")
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, auth_service: AuthService):
        """測試 Email 重複錯誤"""
        email = "duplicate@example.com"
        username1 = "user1"
        username2 = "user2"
        password = "password123"

        # 建立第一個用戶
        await auth_service.create_user(email, username1, password)

        # 嘗試使用相同 email 建立第二個用戶
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.create_user(email, username2, password)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, auth_service: AuthService):
        """測試 Username 重複錯誤"""
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        username = "sameusername"
        password = "password123"

        # 建立第一個用戶
        await auth_service.create_user(email1, username, password)

        # 嘗試使用相同 username 建立第二個用戶
        with pytest.raises(ValueError, match="Username already taken"):
            await auth_service.create_user(email2, username, password)


class TestAuthenticateUser:
    """用戶驗證測試"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service: AuthService):
        """測試成功驗證"""
        email = "auth@example.com"
        username = "authuser"
        password = "password123"

        # 建立用戶
        created_user = await auth_service.create_user(email, username, password)

        # 驗證用戶
        authenticated_user = await auth_service.authenticate_user(username, password)

        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.email == email
        assert authenticated_user.username == username

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service: AuthService):
        """測試密碼錯誤"""
        email = "auth@example.com"
        username = "authuser"
        password = "password123"
        wrong_password = "wrongpassword"

        # 建立用戶
        await auth_service.create_user(email, username, password)

        # 使用錯誤密碼驗證
        authenticated_user = await auth_service.authenticate_user(username, wrong_password)

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service: AuthService):
        """測試用戶不存在"""
        authenticated_user = await auth_service.authenticate_user("nonexistent", "password")

        assert authenticated_user is None
