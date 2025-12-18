# /backend/app/services/theme_service.py

class ThemeManager:
    
    AVAILABLE_THEMES = {
        "light": {
            "name": "Light Mode",
            "colors": {...},  # Light colors
            "description": "Default light theme"
        },
        "dark": {
            "name": "Dark Mode",
            "colors": {...},  # Dark colors
            "description": "Dark mode for reduced eye strain"
        },
        "high-contrast": {
            "name": "High Contrast",
            "colors": {...},  # High contrast colors
            "description": "For accessibility"
        }
    }
    
    @staticmethod
    async def apply_theme(
        db: AsyncSession,
        user_id: str,
        theme_name: str
    ) -> Dict:
        """Apply theme to user"""
        
        if theme_name not in ThemeManager.AVAILABLE_THEMES:
            raise BadRequestError(ErrorCode.VALIDATION_ERROR, f"Theme not found: {theme_name}")
        
        user = await db.get(User, user_id)
        user.theme = theme_name
        await db.commit()
        
        return {
            "message": "Theme applied",
            "theme": theme_name
        }
