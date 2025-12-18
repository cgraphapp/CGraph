"""
SEO meta tags and Open Graph implementation
"""

from fastapi import Request
from fastapi.responses import HTMLResponse

class SEOMiddleware:
    
    @staticmethod
    def get_meta_tags(request: Request, page_type: str, data: dict = None) -> str:
        """
        Generate meta tags and Open Graph tags
        """
        
        meta_tags = {
            'home': {
                'title': 'CGRAPH - Enterprise Messaging Platform',
                'description': 'Secure, encrypted messaging for teams and communities',
                'image': 'https://cgraph.org/og-image.png',
                'url': 'https://cgraph.org'
            },
            'room': {
                'title': f"{data.get('room_name', 'Room')} - CGRAPH",
                'description': data.get('room_description', 'Join our community'),
                'image': data.get('room_image', 'https://cgraph.org/og-default.png'),
                'url': f"https://cgraph.org/rooms/{data.get('room_id')}"
            },
            'user_profile': {
                'title': f"{data.get('username', 'User')} - CGRAPH",
                'description': data.get('bio', 'Member of CGRAPH'),
                'image': data.get('avatar_url', 'https://cgraph.org/default-avatar.png'),
                'url': f"https://cgraph.org/users/{data.get('user_id')}"
            }
        }
        
        config = meta_tags.get(page_type, meta_tags['home'])
        
        return f"""
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{config['title']}</title>
        <meta name="description" content="{config['description']}">
        
        <!-- Open Graph -->
        <meta property="og:title" content="{config['title']}">
        <meta property="og:description" content="{config['description']}">
        <meta property="og:image" content="{config['image']}">
        <meta property="og:url" content="{config['url']}">
        <meta property="og:type" content="website">
        
        <!-- Twitter Card -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{config['title']}">
        <meta name="twitter:description" content="{config['description']}">
        <meta name="twitter:image" content="{config['image']}">
        
        <!-- Canonical URL -->
        <link rel="canonical" href="{config['url']}">
        """
