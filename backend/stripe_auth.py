import stripe
import os
from dotenv import load_dotenv


load_dotenv()



class StripeAuth:
    def __init__(self):
        self.stripe_api_key = os.getenv('STRIPE_API_KEY')
        if not self.stripe_api_key:
            raise ValueError("STRIPE_API_KEY is not set")
        stripe.api_key = self.stripe_api_key

    #create charge and return the receipt url
    def create_charge(self, amount, currency, source, description):
        charge = stripe.Charge.create(
            amount=amount,
            currency=currency,
            source=source,
            description=description
        )
        return charge.receipt_url
    





