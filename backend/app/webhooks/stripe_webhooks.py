"""
Complete Stripe webhook handler for payments and subscriptions
"""

import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from app.services.payment_service import PaymentService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

WEBHOOK_EVENTS = {
    'charge.succeeded': handle_charge_succeeded,
    'charge.failed': handle_charge_failed,
    'charge.refunded': handle_charge_refunded,
    'invoice.payment_succeeded': handle_invoice_succeeded,
    'invoice.payment_failed': handle_invoice_failed,
    'customer.subscription.created': handle_subscription_created,
    'customer.subscription.updated': handle_subscription_updated,
    'customer.subscription.deleted': handle_subscription_deleted,
    'payment_intent.succeeded': handle_payment_intent_succeeded,
    'payment_intent.payment_failed': handle_payment_intent_failed,
}

@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhooks
    Stripe sends events for:
    - Payment intents (succeeded, failed)
    - Charges (succeeded, failed, refunded)
    - Invoices (payment_succeeded, payment_failed)
    - Subscriptions (created, updated, deleted)
    """

    # Get payload and signature
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    if not sig_header:
        logger.warning("Missing Stripe signature header")
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    event_type = event['type']
    event_data = event['data']['object']

    logger.info(f"Processing Stripe webhook: {event_type}")

    handler = WEBHOOK_EVENTS.get(event_type)
    if handler:
        try:
            await handler(event_data)
        except Exception as e:
            logger.error(f"Error handling {event_type}: {str(e)}")
            # Don't raise - return 200 to prevent Stripe from retrying
    else:
        logger.warning(f"No handler for event type: {event_type}")

    return {"status": "received"}

async def handle_charge_succeeded(charge_data: dict):
    """Handle successful charge"""
    customer_id = charge_data.get('customer')
    amount = charge_data.get('amount') / 100  # Convert from cents
    
    logger.info(f"Charge succeeded: {customer_id}, amount: {amount}")
    
    await PaymentService.log_charge(
        stripe_customer_id=customer_id,
        amount=amount,
        status='succeeded'
    )

async def handle_charge_failed(charge_data: dict):
    """Handle failed charge"""
    customer_id = charge_data.get('customer')
    reason = charge_data.get('failure_reason')
    
    logger.warning(f"Charge failed for {customer_id}: {reason}")
    
    await PaymentService.log_charge(
        stripe_customer_id=customer_id,
        status='failed',
        failure_reason=reason
    )
    
    # Send email to user
    await notify_payment_failed(customer_id, reason)

async def handle_charge_refunded(charge_data: dict):
    """Handle refunded charge"""
    customer_id = charge_data.get('customer')
    amount = charge_data.get('amount_refunded') / 100
    
    logger.info(f"Charge refunded: {customer_id}, amount: {amount}")
    
    await PaymentService.log_refund(
        stripe_customer_id=customer_id,
        amount=amount
    )

async def handle_payment_intent_succeeded(payment_intent: dict):
    """Handle successful payment intent"""
    customer_id = payment_intent.get('customer')
    amount = payment_intent.get('amount') / 100
    
    # Update subscription if exists
    await PaymentService.activate_subscription(customer_id)

async def handle_subscription_created(subscription: dict):
    """Handle new subscription"""
    customer_id = subscription.get('customer')
    plan = subscription.get('items')['data']['plan']['id']
    
    await PaymentService.create_subscription(
        stripe_customer_id=customer_id,
        plan=plan,
        status='active'
    )

async def handle_subscription_updated(subscription: dict):
    """Handle subscription update"""
    customer_id = subscription.get('customer')
    status = subscription.get('status')
    
    await PaymentService.update_subscription_status(
        stripe_customer_id=customer_id,
        status=status
    )

async def handle_subscription_deleted(subscription: dict):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')
    
    await PaymentService.cancel_subscription(
        stripe_customer_id=customer_id
    )
    
    # Send cancellation email
    await notify_subscription_cancelled(customer_id)