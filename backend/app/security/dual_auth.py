# /backend/app/security/dual_auth.py
"""
Dual authentication system: Email + MFA
Supports TOTP, Backup codes, SMS codes
"""

import pyotp
import qrcode
import secrets
from io import BytesIO
import base64

class DualAuthenticationManager:
    
    async def register_with_email(
        self,
        db: AsyncSession,
        email: str,
        username: str,
        password: str
    ) -> Dict:
        """
        Register user with email
        Step 1 of dual auth
        """
        
        # Validate email
        if not self._is_valid_email(email):
            raise BadRequestError(ErrorCode.INVALID_EMAIL, "Invalid email format")
        
        # Check if exists
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar():
            raise ConflictError(ErrorCode.EMAIL_TAKEN, "Email already registered")
        
        # Create user (unverified)
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            auth_method="email",
            email_verified=False,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Send verification email
        verification_token = secrets.token_urlsafe(32)
        await cache.setex(
            f"email_verify:{user.id}",
            3600,  # 1 hour
            verification_token
        )
        
        # Send email
        await email_service.send_email(
            to=email,
            subject="Verify your CGRAPH email",
            template="verify_email",
            context={
                "username": username,
                "verify_link": f"https://app.cgraph.org/verify?token={verification_token}&user_id={user.id}"
            }
        )
        
        return {
            "user_id": str(user.id),
            "email": email,
            "message": "Verification email sent"
        }
    
    async def verify_email(self, db: AsyncSession, user_id: str, token: str) -> Dict:
        """
        Verify email address
        Step 2 of dual auth
        """
        
        # Get user
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundError("User")
        
        # Check token
        stored_token = await cache.get(f"email_verify:{user_id}")
        if not stored_token or stored_token != token:
            raise BadRequestError(ErrorCode.INVALID_TOKEN, "Invalid or expired verification token")
        
        # Mark verified
        user.email_verified = True
        await db.commit()
        
        # Delete token
        await cache.delete(f"email_verify:{user_id}")
        
        return {
            "message": "Email verified successfully",
            "next_step": "Setup MFA"
        }
    
    async def setup_mfa_totp(self, db: AsyncSession, user_id: str) -> Dict:
        """
        Setup TOTP (Time-based One-Time Password) MFA
        Uses authenticator apps (Google Authenticator, Authy, etc.)
        """
        
        user = await db.get(User, user_id)
        if not user:
            raise NotFoundError("User")
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="CGRAPH"
        )
        
        # Create QR image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Generate backup codes
        backup_codes = [
            secrets.token_hex(4).upper() for _ in range(10)
        ]
        
        # Store temporarily
        mfa_setup = {
            "secret": secret,
            "backup_codes": backup_codes,
            "setup_at": datetime.utcnow().isoformat()
        }
        
        await cache.setex(
            f"mfa_setup:{user_id}",
            900,  # 15 minutes
            json.dumps(mfa_setup)
        )
        
        return {
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "secret": secret,
            "backup_codes": backup_codes,
            "instructions": "Scan QR code with authenticator app (Google Authenticator, Authy, Microsoft Authenticator)"
        }
    
    async def verify_mfa_totp(
        self,
        db: AsyncSession,
        user_id: str,
        code: str
    ) -> Dict:
        """
        Verify TOTP code and enable MFA
        """
        
        # Get setup data
        mfa_setup = await cache.get(f"mfa_setup:{user_id}")
        if not mfa_setup:
            raise BadRequestError(ErrorCode.VALIDATION_ERROR, "MFA setup expired, start over")
        
        setup_data = json.loads(mfa_setup)
        secret = setup_data['secret']
        
        # Verify code
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            raise BadRequestError(ErrorCode.VALIDATION_ERROR, "Invalid MFA code")
        
        # Update user
        user = await db.get(User, user_id)
        user.mfa_enabled = True
        user.mfa_type = "totp"
        user.mfa_secret = secret
        user.mfa_backup_codes = setup_data['backup_codes']
        
        await db.commit()
        
        # Clean up
        await cache.delete(f"mfa_setup:{user_id}")
        
        return {
            "message": "MFA enabled successfully",
            "backup_codes": setup_data['backup_codes'],
            "important": "Save these backup codes in a secure place"
        }
    
    async def login_with_email_mfa(
        self,
        db: AsyncSession,
        email: str,
        password: str
    ) -> Dict:
        """
        Login with email + password
        Returns MFA challenge if enabled
        """
        
        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar()
        
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError(ErrorCode.INVALID_CREDENTIALS, "Invalid email or password")
        
        if not user.email_verified:
            raise UnauthorizedError(ErrorCode.VALIDATION_ERROR, "Please verify your email first")
        
        if not user.is_active:
            raise ForbiddenError(ErrorCode.FORBIDDEN, "Account disabled")
        
        # Check if MFA enabled
        if user.mfa_enabled:
            # Generate MFA challenge
            mfa_challenge = secrets.token_urlsafe(32)
            
            # Store challenge
            await cache.setex(
                f"mfa_challenge:{mfa_challenge}",
                300,  # 5 minutes
                json.dumps({
                    "user_id": str(user.id),
                    "email": email,
                    "created_at": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "requires_mfa": True,
                "mfa_challenge": mfa_challenge,
                "mfa_type": user.mfa_type
            }
        
        # No MFA, generate token
        access_token = create_access_token(str(user.id))
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "expires_in": 3600
        }
    
    async def verify_mfa_code_login(
        self,
        db: AsyncSession,
        mfa_challenge: str,
        code: str
    ) -> Dict:
        """
        Verify MFA code during login
        """
        
        # Get challenge
        challenge_data = await cache.get(f"mfa_challenge:{mfa_challenge}")
        if not challenge_data:
            raise UnauthorizedError(ErrorCode.INVALID_TOKEN, "MFA challenge expired")
        
        data = json.loads(challenge_data)
        user = await db.get(User, data['user_id'])
        
        # Verify TOTP code
        totp = pyotp.TOTP(user.mfa_secret)
        
        if not totp.verify(code, valid_window=1):
            # Check backup codes
            if code not in user.mfa_backup_codes:
                raise UnauthorizedError(ErrorCode.INVALID_TOKEN, "Invalid MFA code")
            
            # Remove used backup code
            user.mfa_backup_codes.remove(code)
            await db.commit()
        
        # Delete challenge
        await cache.delete(f"mfa_challenge:{mfa_challenge}")
        
        # Generate token
        access_token = create_access_token(str(user.id))
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "expires_in": 3600
        }

# API Endpoints
@router.post("/auth/email/register")
async def email_register(
    email: str,
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Step 1: Register with email"""
    return await DualAuthenticationManager.register_with_email(
        db, email, username, password
    )

@router.post("/auth/email/verify")
async def email_verify(
    user_id: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """Step 2: Verify email"""
    return await DualAuthenticationManager.verify_email(db, user_id, token)

@router.post("/auth/mfa/setup")
async def mfa_setup(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Step 3: Setup MFA"""
    return await DualAuthenticationManager.setup_mfa_totp(db, current_user)

@router.post("/auth/mfa/verify")
async def mfa_verify(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Step 4: Verify MFA"""
    return await DualAuthenticationManager.verify_mfa_totp(db, current_user, code)

@router.post("/auth/login")
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """Login with email (+ MFA if enabled)"""
    return await DualAuthenticationManager.login_with_email_mfa(db, email, password)

@router.post("/auth/mfa/verify-login")
async def verify_mfa_login(
    mfa_challenge: str,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify MFA code during login"""
    return await DualAuthenticationManager.verify_mfa_code_login(db, mfa_challenge, code)
