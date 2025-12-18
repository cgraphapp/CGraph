"""
Handle SendGrid webhook events (delivery, open, click, bounce)
"""

from fastapi import APIRouter, Request
import json
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhooks/sendgrid")
async def handle_sendgrid_webhook(request: Request):
    """
    Handle SendGrid events:
    - processed
    - dropped
    - delivered
    - deferred
    - bounce
    - open
    - click
    - unsubscribe
    - group_unsubscribe
    - group_resubscribe
    """

    body = await request.json()

    # Verify webhook signature
    if not verify_sendgrid_signature(request, body):
        logger.warning("Invalid SendGrid webhook signature")
        return {"status": "invalid_signature"}

    # Process events
    for event in body:
        event_type = event.get('event')
        email = event.get('email')
        timestamp = event.get('timestamp')

        logger.info(f"SendGrid event: {event_type} for {email}")

        if event_type == 'delivered':
            await log_email_delivered(email, timestamp)
        elif event_type == 'bounce':
            await handle_email_bounce(email, event.get('reason'))
        elif event_type == 'drop':
            await log_email_dropped(email, event.get('reason'))
        elif event_type == 'open':
            await log_email_opened(email, timestamp)
        elif event_type == 'click':
            await log_email_clicked(email, event.get('url'), timestamp)
        elif event_type == 'unsubscribe':
            await handle_unsubscribe(email)

    return {"status": "ok"}

def verify_sendgrid_signature(request: Request, body: dict) -> bool:
    """Verify SendGrid webhook signature"""
    signature = request.headers.get('X-Twilio-Email-Event-Webhook-Signature')
    timestamp = request.headers.get('X-Twilio-Email-Event-Webhook-Timestamp')
    
    if not signature or not timestamp:
        return False

    # Reconstruct signed content
    signed_content = f"{timestamp}{json.dumps(body, separators=(',', ':'), sort_keys=True)}"
    
    # Create HMAC
    expected_signature = hmac.new(
        settings.SENDGRID_WEBHOOK_SECRET.encode(),
        signed_content.encode(),
        hashlib.sha256
    ).digest()
    
    # Compare (timing-safe comparison)
    return hmac.compare_digest(
        signature.encode(),
        base64.b64encode(expected_signature)
    )