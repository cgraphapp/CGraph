# /backend/app/security/wallet_auth_complete.py
"""
Wallet authentication: Cryptographic keypair-based anonymous login
ED25519 elliptic curve (same as Signal, WireGuard)
"""

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import secrets

class WalletAuthComplete:
    
    async def create_wallet(self, db: AsyncSession) -> Dict:
        """
        Create new cryptographic wallet
        Generates ED25519 keypair locally (client-side in production)
        """
        
        # Generate keypair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Create wallet ID
        wallet_id = secrets.token_hex(16)
        
        # Create user
        user = User(
            username=f"wallet_{wallet_id}",
            wallet_id=wallet_id,
            wallet_public_key=public_pem,
            auth_method="wallet",
            is_anonymous=True,
            is_active=True
        )
        
        db.add(user)
        await db.commit()
        
        return {
            "wallet_id": wallet_id,
            "user_id": str(user.id),
            "private_key": private_pem,  # STORE SECURELY ON CLIENT
            "public_key": public_pem
        }
    
    async def get_login_challenge(self, db: AsyncSession, wallet_id: str) -> str:
        """
        Get random challenge for wallet login
        User must sign this with their private key
        """
        
        # Verify wallet exists
        user = await db.execute(select(User).where(User.wallet_id == wallet_id))
        if not user.scalar():
            raise NotFoundError("Wallet")
        
        # Generate challenge
        challenge = secrets.token_hex(32)  # 64 hex chars = 256 bits
        
        # Store in cache (5 minutes)
        await cache.setex(
            f"wallet_challenge:{wallet_id}",
            300,
            challenge
        )
        
        return challenge
    
    async def verify_wallet_signature(
        self,
        db: AsyncSession,
        wallet_id: str,
        challenge: str,
        signature_hex: str
    ) -> Dict:
        """
        Verify wallet signature and login
        """
        
        # Get user
        result = await db.execute(select(User).where(User.wallet_id == wallet_id))
        user = result.scalar()
        if not user:
            raise NotFoundError("Wallet")
        
        # Get challenge from cache
        cached_challenge = await cache.get(f"wallet_challenge:{wallet_id}")
        if not cached_challenge or cached_challenge != challenge:
            raise UnauthorizedError(ErrorCode.INVALID_TOKEN, "Challenge expired or invalid")
        
        # Verify signature
        try:
            public_key = serialization.load_pem_public_key(
                user.wallet_public_key.encode('utf-8')
            )
            signature_bytes = bytes.fromhex(signature_hex)
            
            public_key.verify(
                signature_bytes,
                challenge.encode('utf-8')
            )
        except Exception as e:
            raise UnauthorizedError(ErrorCode.INVALID_TOKEN, "Invalid signature")
        
        # Delete challenge (one-time use)
        await cache.delete(f"wallet_challenge:{wallet_id}")
        
        # Generate token
        access_token = create_access_token(str(user.id))
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "wallet_id": wallet_id,
            "expires_in": 3600
        }

# API Endpoints
@router.post("/auth/wallet/create")
async def create_wallet(db: AsyncSession = Depends(get_db)):
    """Create new wallet"""
    return await WalletAuthComplete.create_wallet(db)

@router.post("/auth/wallet/challenge")
async def wallet_challenge(
    wallet_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get challenge for wallet login"""
    challenge = await WalletAuthComplete.get_login_challenge(db, wallet_id)
    return {"challenge": challenge}

@router.post("/auth/wallet/verify")
async def verify_wallet(
    wallet_id: str,
    challenge: str,
    signature: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify wallet signature"""
    return await WalletAuthComplete.verify_wallet_signature(
        db, wallet_id, challenge, signature
    )
