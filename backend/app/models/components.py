# /backend/app/models/components.py

class ComponentLibrary(Base):
    __tablename__ = "component_library"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    figma_id = Column(String(255))
    figma_file_id = Column(String(255))
    description = Column(Text)
    component_path = Column(String(500))
    
    # Visual assets
    svg_url = Column(String(500))
    png_url = Column(String(500))
    
    # Properties
    properties = Column(JSONB)  # Component properties from Figma
    bounds = Column(JSONB)  # Size/position
    
    # Code
    code_react = Column(Text)  # React component code
    code_vue = Column(Text)  # Vue component code
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)

# Endpoint to get component code
@router.get("/components/{component_id}/code")
async def get_component_code(
    component_id: str,
    format: str = "react",  # react or vue
    db: AsyncSession = Depends(get_db)
):
    """Get component code in requested format"""
    
    component = await db.get(ComponentLibrary, component_id)
    if not component:
        raise NotFoundError("Component")
    
    if format == "react":
        return {"code": component.code_react}
    elif format == "vue":
        return {"code": component.code_vue}
    else:
        raise BadRequestError(ErrorCode.VALIDATION_ERROR, f"Unsupported format: {format}")
