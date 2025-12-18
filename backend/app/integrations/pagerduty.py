"""
PagerDuty integration for incident management
"""

import pdpyras
import logging

logger = logging.getLogger(__name__)

class PagerDutyManager:
    
    def __init__(self, api_token: str):
        self.session = pdpyras.APISession(api_token)
    
    async def trigger_incident(
        self,
        service_id: str,
        title: str,
        description: str,
        severity: str = "error"  # critical, error, warning, info
    ) -> dict:
        """
        Trigger PagerDuty incident
        """
        
        try:
            event = self.session.post(
                "/incidents",
                json={
                    "incidents": [
                        {
                            "type": "incident",
                            "title": title,
                            "description": description,
                            "service": {
                                "id": service_id,
                                "type": "service_reference"
                            },
                            "urgency": severity
                        }
                    ]
                }
            )
            
            logger.info(f"PagerDuty incident triggered: {event['incidents']['id']}")
            return event
        
        except Exception as e:
            logger.error(f"Failed to trigger incident: {str(e)}")
            return None
    
    async def resolve_incident(self, incident_id: str) -> bool:
        """Resolve PagerDuty incident"""
        
        try:
            self.session.put(
                f"/incidents/{incident_id}",
                json={"incidents": [{"id": incident_id, "status": "resolved"}]}
            )
            
            logger.info(f"PagerDuty incident resolved: {incident_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to resolve incident: {str(e)}")
            return False

# Usage in alert handler
async def handle_high_error_rate():
    """Handle high error rate alert"""
    
    pd_manager = PagerDutyManager(settings.PAGERDUTY_API_TOKEN)
    
    await pd_manager.trigger_incident(
        service_id="PXYZ123",
        title="High error rate detected in CGRAPH API",
        description="Error rate exceeded 5% threshold",
        severity="critical"
    )