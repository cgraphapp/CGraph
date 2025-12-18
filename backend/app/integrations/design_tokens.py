# /backend/app/integrations/design_tokens.py
"""
Export design tokens (colors, typography, spacing) in multiple formats
Supports Figma tokens, CSS variables, JSON
"""

class DesignTokenManager:
    
    DESIGN_TOKENS = {
        "colors": {
            "primary": "#3b82f6",
            "secondary": "#10b981",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "success": "#22c55e",
            "gray-50": "#f9fafb",
            "gray-100": "#f3f4f6",
            "gray-200": "#e5e7eb",
            "gray-300": "#d1d5db",
            "gray-400": "#9ca3af",
            "gray-500": "#6b7280",
            "gray-600": "#4b5563",
            "gray-700": "#374151",
            "gray-800": "#1f2937",
            "gray-900": "#111827"
        },
        "typography": {
            "fontFamily": {
                "base": "'Inter', -apple-system, sans-serif",
                "mono": "'JetBrains Mono', monospace"
            },
            "fontSize": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
                "4xl": "2.25rem"
            },
            "fontWeight": {
                "light": 300,
                "normal": 400,
                "medium": 500,
                "semibold": 600,
                "bold": 700
            },
            "lineHeight": {
                "tight": 1.2,
                "normal": 1.5,
                "relaxed": 1.75
            }
        },
        "spacing": {
            "0": "0",
            "1": "0.25rem",
            "2": "0.5rem",
            "3": "0.75rem",
            "4": "1rem",
            "6": "1.5rem",
            "8": "2rem",
            "12": "3rem",
            "16": "4rem",
            "20": "5rem",
            "24": "6rem",
            "32": "8rem"
        },
        "borderRadius": {
            "none": "0",
            "sm": "0.375rem",
            "base": "0.5rem",
            "md": "0.75rem",
            "lg": "1rem",
            "full": "9999px"
        },
        "shadows": {
            "xs": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
            "sm": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
        }
    }
    
    @staticmethod
    def export_as_css() -> str:
        """Export tokens as CSS variables"""
        
        css = ":root {\n"
        
        # Colors
        for name, value in DesignTokenManager.DESIGN_TOKENS["colors"].items():
            css += f"  --color-{name}: {value};\n"
        
        # Typography
        for key, group in DesignTokenManager.DESIGN_TOKENS["typography"].items():
            if isinstance(group, dict):
                for name, value in group.items():
                    if isinstance(value, (int, float)):
                        css += f"  --{key}-{name}: {value};\n"
                    else:
                        css += f"  --{key}-{name}: {value};\n"
        
        # Spacing
        for name, value in DesignTokenManager.DESIGN_TOKENS["spacing"].items():
            css += f"  --space-{name}: {value};\n"
        
        # Border Radius
        for name, value in DesignTokenManager.DESIGN_TOKENS["borderRadius"].items():
            css += f"  --radius-{name}: {value};\n"
        
        # Shadows
        for name, value in DesignTokenManager.DESIGN_TOKENS["shadows"].items():
            css += f"  --shadow-{name}: {value};\n"
        
        css += "}\n"
        
        return css
    
    @staticmethod
    def export_as_json() -> Dict:
        """Export tokens as JSON"""
        return DesignTokenManager.DESIGN_TOKENS
    
    @staticmethod
    def export_for_figma() -> Dict:
        """Export tokens in Figma token format"""
        
        figma_tokens = {}
        
        for category, tokens in DesignTokenManager.DESIGN_TOKENS.items():
            figma_tokens[category] = {}
            
            if isinstance(tokens, dict):
                for name, value in tokens.items():
                    if isinstance(value, dict):
                        for sub_name, sub_value in value.items():
                            figma_tokens[category][f"{name}/{sub_name}"] = {
                                "value": sub_value,
                                "type": category
                            }
                    else:
                        figma_tokens[category][name] = {
                            "value": value,
                            "type": category
                        }
        
        return figma_tokens
    
    @staticmethod
    def export_as_tailwind() -> str:
        """Export tokens as Tailwind config"""
        
        config = """
module.exports = {
  theme: {
    extend: {
      colors: {
"""
        
        for name, value in DesignTokenManager.DESIGN_TOKENS["colors"].items():
            config += f"        '{name}': '{value}',\n"
        
        config += """      },
      spacing: {
"""
        
        for name, value in DesignTokenManager.DESIGN_TOKENS["spacing"].items():
            config += f"        '{name}': '{value}',\n"
        
        config += """      },
      borderRadius: {
"""
        
        for name, value in DesignTokenManager.DESIGN_TOKENS["borderRadius"].items():
            config += f"        '{name}': '{value}',\n"
        
        config += """      },
      boxShadow: {
"""
        
        for name, value in DesignTokenManager.DESIGN_TOKENS["shadows"].items():
            config += f"        '{name}': '{value}',\n"
        
        config += """      }
    }
  }
}
"""
        
        return config

# Export endpoints
@router.get("/design/tokens/css")
async def get_tokens_css():
    """Get design tokens as CSS variables"""
    css = DesignTokenManager.export_as_css()
    return Response(content=css, media_type="text/css")

@router.get("/design/tokens/json")
async def get_tokens_json():
    """Get design tokens as JSON"""
    return DesignTokenManager.export_as_json()

@router.get("/design/tokens/figma")
async def get_tokens_figma():
    """Get design tokens for Figma"""
    return DesignTokenManager.export_for_figma()

@router.get("/design/tokens/tailwind")
async def get_tokens_tailwind():
    """Get design tokens as Tailwind config"""
    config = DesignTokenManager.export_as_tailwind()
    return Response(content=config, media_type="application/javascript")
