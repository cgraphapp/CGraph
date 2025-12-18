# /backend/app/integrations/figma/figma_client.py
"""
Figma API integration for automatic UI import
Syncs designs directly from Figma to component library
"""

import httpx
import asyncio
import json
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class FigmaClient:
    
    def __init__(self, figma_token: str):
        self.figma_token = figma_token
        self.base_url = "https://api.figma.com/v1"
        self.client = httpx.AsyncClient(
            headers={"X-Figma-Token": figma_token}
        )
    
    async def get_file(self, file_id: str) -> Dict:
        """Get Figma file with all components"""
        
        response = await self.client.get(f"{self.base_url}/files/{file_id}")
        return response.json()
    
    async def get_components(self, file_id: str, library_only: bool = True) -> List[Dict]:
        """
        Extract all components from Figma file
        Returns component metadata, frames, and properties
        """
        
        file_data = await self.get_file(file_id)
        components = []
        
        def traverse_nodes(node, path=""):
            """Recursively traverse Figma nodes"""
            
            if node.get('type') == 'COMPONENT':
                components.append({
                    'id': node['id'],
                    'name': node['name'],
                    'description': node.get('description', ''),
                    'path': f"{path}/{node['name']}",
                    'type': 'COMPONENT',
                    'properties': node.get('componentPropertyDefinitions', {}),
                    'bounds': {
                        'x': node.get('absoluteBoundingBox', {}).get('x'),
                        'y': node.get('absoluteBoundingBox', {}).get('y'),
                        'width': node.get('absoluteBoundingBox', {}).get('width'),
                        'height': node.get('absoluteBoundingBox', {}).get('height')
                    },
                    'fills': node.get('fills', []),
                    'strokes': node.get('strokes', []),
                    'effects': node.get('effects', [])
                })
            
            # Recurse into children
            if 'children' in node:
                for child in node['children']:
                    traverse_nodes(child, f"{path}/{node['name']}")
        
        for node in file_data.get('document', {}).get('children', []):
            traverse_nodes(node)
        
        logger.info(f"Extracted {len(components)} components from Figma file")
        return components
    
    async def export_component_as_svg(self, file_id: str, node_ids: List[str]) -> Dict[str, str]:
        """
        Export components as SVG
        Returns dict of node_id -> SVG URL
        """
        
        response = await self.client.get(
            f"{self.base_url}/files/{file_id}/exports",
            params={
                "ids": ",".join(node_ids),
                "format": "svg",
                "scale": 2
            }
        )
        
        data = response.json()
        return data.get('images', {})
    
    async def export_component_as_png(self, file_id: str, node_ids: List[str]) -> Dict[str, str]:
        """Export components as PNG"""
        
        response = await self.client.get(
            f"{self.base_url}/files/{file_id}/exports",
            params={
                "ids": ",".join(node_ids),
                "format": "png",
                "scale": 2
            }
        )
        
        return response.json().get('images', {})
    
    async def get_component_properties(self, file_id: str, component_id: str) -> Dict:
        """
        Get component properties and variants
        Used for code generation
        """
        
        file_data = await self.get_file(file_id)
        
        def find_component(node):
            if node.get('id') == component_id:
                return node
            for child in node.get('children', []):
                result = find_component(child)
                if result:
                    return result
            return None
        
        component = find_component(file_data.get('document', {}))
        
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        return {
            'id': component['id'],
            'name': component['name'],
            'description': component.get('description', ''),
            'properties': component.get('componentPropertyDefinitions', {}),
            'variants': component.get('componentVariants', [])
        }

# API Endpoint for syncing Figma designs
@router.post("/admin/design-sync/figma")
async def sync_figma_designs(
    figma_file_id: str,
    figma_token: str = Depends(get_admin_token)
):
    """
    Sync Figma designs to component library
    """
    
    try:
        client = FigmaClient(figma_token)
        components = await client.get_components(figma_file_id)
        
        # Export as SVG and PNG
        node_ids = [c['id'] for c in components]
        svgs = await client.export_component_as_svg(figma_file_id, node_ids)
        pngs = await client.export_component_as_png(figma_file_id, node_ids)
        
        # Store in database
        for component in components:
            comp_record = ComponentLibrary(
                name=component['name'],
                figma_id=component['id'],
                figma_file_id=figma_file_id,
                description=component['description'],
                component_path=component['path'],
                properties=json.dumps(component['properties']),
                svg_url=svgs.get(component['id']),
                png_url=pngs.get(component['id']),
                bounds=json.dumps(component['bounds'])
            )
            db.add(comp_record)
        
        await db.commit()
        
        logger.info(f"Synced {len(components)} components from Figma")
        
        return {
            "status": "success",
            "components_synced": len(components),
            "file_id": figma_file_id
        }
    
    except Exception as e:
        logger.error(f"Figma sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Design sync failed")
