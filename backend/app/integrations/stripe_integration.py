# /backend/app/integrations/stripe_integration.py
"""
Complete Stripe integration
- Products and pricing
- Subscriptions
- One-time payments
- Webhooks
"""

import stripe
from app.config import settings
from app.models.subscription import Subscription
from app.services.message_queue import message_queue, Events
from datetime import datetime, timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """
    Stripe payment processing
    """
    
    # Product IDs (from Stripe dashboard)
    PRODUCTS = {
        'premium': 'prod_premium_cgraph',
        'enterprise': 'prod_enterprise_cgraph'
    }
    
    # Price IDs (from Stripe dashboard)
    PRICES = {
        'premium_monthly': 'price_premium_monthly',
        'premium_annual': 'price_premium_annual',
        'enterprise_monthly': 'price_enterprise_monthly'
    }
    
    @staticmethod
    async def create_customer(user_id: str, email: str, name: str):
        """Create Stripe customer"""
        
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={'user_id': user_id}
        )
        
        return customer.id
    
    @staticmethod
    async def create_checkout_session(
        user_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ):
        """Create Stripe checkout session"""
        
        # Get or create customer
        user = await db.get(User, user_id)
        
        if not user.stripe_customer_id:
            user.stripe_customer_id = await StripeService.create_customer(
                user_id,
                user.email,
                user.username
            )
        
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1
                }
            ],
            mode='subscription',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={'user_id': user_id}
        )
        
        return session
    
    @staticmethod
    async def handle_checkout_completed(event_data: dict):
        """Handle checkout session completed"""
        
        session_id = event_data['id']
        session = stripe.checkout.Session.retrieve(session_id)
        
        user_id = session.metadata.get('user_id')
        subscription_id = session.subscription
        
        # Create subscription record
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=subscription_id,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(subscription)
        await db.commit()
        
        # Publish event
        await message_queue.publish_event(
            'payments',
            {
                'type': Events.PAYMENT_COMPLETED,
                'user_id': user_id,
                'subscription_id': subscription_id,
                'tier': session.metadata.get('tier', 'premium')
            }
        )
    
    @staticmethod
    async def handle_webhook(payload: dict, sig_header: str):
        """Process Stripe webhook"""
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return {'status': 'invalid_payload'}
        except stripe.error.SignatureVerificationError:
            return {'status': 'invalid_signature'}
        
        # Route to handler
        event_type = event['type']
        
        if event_type == 'checkout.session.completed':
            await StripeService.handle_checkout_completed(event['data']['object'])
        
        elif event_type == 'customer.subscription.updated':
            # Handle subscription update
            pass
        
        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            pass
        
        elif event_type == 'invoice.payment_failed':
            # Handle payment failure
            pass
        
        return {'status': 'received'}

# API Endpoints

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook endpoint"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    result = await StripeService.handle_webhook(payload, sig_header)
    return result

@router.get("/pricing")
async def get_pricing():
    """Get available pricing plans"""
    
    return {
        'currency': 'usd',
        'plans': [
            {
                'id': 'premium_monthly',
                'name': 'Premium Monthly',
                'price': 9.99,
                'billing_period': 'monthly',
                'features': [
                    'Encrypted messaging',
                    'Group chats up to 100',
                    'File sharing',
                    '30-day message history'
                ]
            },
            {
                'id': 'premium_annual',
                'name': 'Premium Annual',
                'price': 99.99,
                'billing_period': 'annual',
                'features': [
                    'All premium features',
                    '1-year billing discount'
                ]
            }
        ]
    }

@router.post("/subscribe/{plan_id}")
async def create_subscription(
    plan_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create subscription"""
    
    # Map plan_id to price_id
    price_id = StripeService.PRICES.get(plan_id)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    session = await StripeService.create_checkout_session(
        current_user,
        price_id,
        success_url='https://cgraph.org/subscribe/success',
        cancel_url='https://cgraph.org/subscribe/cancel'
    )
    
    return {
        'checkout_url': session.url,
        'session_id': session.id
    }
