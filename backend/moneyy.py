"""
Stripe integration service for Gmail Assistant billing
"""
import stripe
import os
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import User, CallUsage, DailyUsage, PaymentIntent
from database import get_db
import logging

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        # Pricing configuration
        self.CALL_PRICE = Decimal("0.75")  # $0.75 per call
        self.FREE_CALLS_PER_DAY = 1
        self.SUBSCRIPTION_PRICE = 999  # $9.99 in cents
        
    def create_customer(self, email: str, name: str = None) -> str:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'service': 'gmail-assistant'}
            )
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise
    
    def create_payment_intent(self, user_id: str, call_count: int = 1) -> Dict:
        """Create a payment intent for pay-per-call"""
        try:
            amount = int(self.CALL_PRICE * call_count * 100)  # Convert to cents
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                metadata={
                    'user_id': user_id,
                    'call_count': call_count,
                    'service': 'gmail-assistant-calls'
                }
            )
            
            # Store payment intent in database
            db = next(get_db())
            payment_intent = PaymentIntent(
                user_id=user_id,
                stripe_payment_intent_id=intent.id,
                amount=Decimal(amount) / 100,
                status=intent.status,
                call_count=call_count
            )
            db.add(payment_intent)
            db.commit()
            db.close()
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': amount
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    def create_subscription(self, customer_id: str) -> Dict:
        """Create a monthly subscription"""
        try:
            # First, create a price if it doesn't exist
            try:
                price = stripe.Price.retrieve("price_gmail_assistant_monthly")
            except stripe.error.InvalidRequestError:
                price = stripe.Price.create(
                    product_data={
                        'name': 'Gmail Assistant Monthly',
                        'description': 'Unlimited voice calls to Gmail Assistant'
                    },
                    unit_amount=self.SUBSCRIPTION_PRICE,
                    currency='usd',
                    recurring={'interval': 'month'}
                )
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price.id}],
                metadata={'service': 'gmail-assistant-subscription'}
            )
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    