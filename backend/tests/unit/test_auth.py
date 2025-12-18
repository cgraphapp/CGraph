import pytest
from app.services.auth import AuthService

def test_hash_password():
    """Test password hashing"""
    password = "SecurePass123!"
    hash_result = AuthService.hash_password(password)
    
    # Verify hash is different from password
    assert hash_result != password
    
    # Verify password matches hash
    assert AuthService.verify_password(password, hash_result)

def test_invalid_password():
    """Test invalid password fails"""
    password = "SecurePass123!"
    hash_result = AuthService.hash_password(password)
    
    # Wrong password should fail
    assert not AuthService.verify_password("WrongPassword", hash_result)

def test_create_access_token():
    """Test JWT token creation"""
    user_id = "test-user-123"
    token = AuthService.create_access_token(user_id)
    
    # Token should not be empty
    assert token
    assert len(token) > 0
    
    # Verify token
    verified_user_id = AuthService.verify_token(token)
    assert verified_user_id == user_id

def test_invalid_token():
    """Test invalid token fails"""
    invalid_token = "invalid.token.here"
    verified = AuthService.verify_token(invalid_token)
    
    assert verified is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
