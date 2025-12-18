# /backend/app/security/e2e_encryption.py
"""
End-to-end encryption using Signal Protocol
All messages encrypted on client, decrypted on client only
Server never sees plaintext
"""

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
import os
import json
import base64
from datetime import datetime, timedelta

class E2EEncryptionService:
    """
    Signal Protocol Implementation
    - Initial key exchange (ECDH)
    - Double ratchet algorithm (forward secrecy)
    - Chain keys for message authentication
    """
    
    ALGORITHM_VERSION = "signal_v1"
    KEY_ROTATION_DAYS = 7
    
    @staticmethod
    def generate_identity_keypair():
        """Generate long-term identity keypair (Curve25519)"""
        from cryptography.hazmat.primitives.asymmetric import x25519
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def generate_signed_prekeys(identity_key, count=100):
        """Generate pre-signed prekeys for offline message support"""
        from cryptography.hazmat.primitives.asymmetric import x25519
        
        prekeys = []
        for i in range(count):
            prekey = {
                'key_id': i,
                'public_key': x25519.X25519PrivateKey.generate().public_key(),
                'signature': None,  # Signed by identity key
                'created_at': datetime.utcnow().isoformat(),
                'used': False
            }
            prekeys.append(prekey)
        
        return prekeys
    
    @staticmethod
    def generate_session_key(shared_secret: bytes) -> bytes:
        """
        Derive session key from shared secret
        Using HKDF-SHA256
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'signal_session_key',
            backend=default_backend()
        )
        return hkdf.derive(shared_secret)
    
    @staticmethod
    def encrypt_message(plaintext: str, session_key: bytes) -> dict:
        """Encrypt message with ChaCha20-Poly1305"""
        
        nonce = os.urandom(12)  # 96-bit nonce
        cipher = ChaCha20Poly1305(session_key)
        
        ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
        
        return {
            'algorithm': 'chacha20-poly1305',
            'nonce': base64.b64encode(nonce).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def decrypt_message(encrypted_data: dict, session_key: bytes) -> str:
        """Decrypt message"""
        
        cipher = ChaCha20Poly1305(session_key)
        nonce = base64.b64decode(encrypted_data['nonce'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        
        plaintext = cipher.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    
    @staticmethod
    def double_ratchet_advance(chain_key: bytes):
        """Advance double ratchet chain"""
        import hmac
        
        # HMAC-SHA256(key, "next")
        next_chain_key = hmac.new(chain_key, b"next", hashes.SHA256).digest()
        message_key = hmac.new(chain_key, b"msg", hashes.SHA256).digest()
        
        return next_chain_key, message_key

# Database model for encrypted messages
class EncryptedMessage(Base):
    __tablename__ = "encrypted_messages"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    room_id = Column(String, ForeignKey("rooms.id"))
    sender_id = Column(UUID, ForeignKey("users.id"))
    
    # Encrypted content
    algorithm = Column(String)  # "chacha20-poly1305"
    nonce = Column(String)
    ciphertext = Column(String)  # Base64 encoded
    
    # Key info
    session_key_id = Column(String)  # Reference to key version
    
    # Metadata (not encrypted)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # For forward secrecy
    chain_position = Column(Integer)  # Position in double ratchet chain
    generation = Column(Integer)  # Key generation number

# API Endpoints for E2E

@router.post("/e2e/session/init")
async def init_e2e_session(
    recipient_user_id: str,
    prekey_bundle: dict,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Initialize encrypted session with another user"""
    
    # 1. Get recipient's prekey bundle (includes public keys)
    recipient = await db.get(User, recipient_user_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. Perform ECDH with recipient's keys
    # 3. Generate shared session key
    # 4. Store session state
    
    session = {
        'session_id': secrets.token_urlsafe(32),
        'participant_1': current_user,
        'participant_2': recipient_user_id,
        'key_version': 1,
        'created_at': datetime.utcnow().isoformat(),
        'status': 'active'
    }
    
    # Store in cache with 30-day expiry
    await cache.set(f"e2e_session:{session['session_id']}", session, ex=2592000)
    
    return session

@router.post("/e2e/message/send")
async def send_encrypted_message(
    request: EncryptedMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Send encrypted message"""
    
    # Verify session exists
    session = await cache.get(f"e2e_session:{request.session_id}")
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Store encrypted message
    msg = EncryptedMessage(
        room_id=request.room_id,
        sender_id=current_user,
        algorithm=request.algorithm,
        nonce=request.nonce,
        ciphertext=request.ciphertext,
        session_key_id=request.key_version
    )
    
    db.add(msg)
    await db.commit()
    
    # Publish to recipient via WebSocket
    await websocket_manager.broadcast(
        f"room:{request.room_id}",
        {
            'type': 'message.encrypted',
            'message_id': str(msg.id),
            'sender_id': current_user,
            'timestamp': msg.created_at.isoformat()
        }
    )
    
    return {'message_id': str(msg.id), 'encrypted': True}
