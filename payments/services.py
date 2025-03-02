import logging
from typing import List, Dict, Optional

import stripe

from payments.models import Item, Order
from stripe_project import settings


logger = logging.getLogger(__name__)


def create_stripe_line_items(items: List[Item]) -> List[Dict]:
    """Создает список элементов для платежной сессии Stripe."""
    if not items:
        raise ValueError("Items list is empty")

    currency = items[0].currency
    line_items = [
        {
            "price_data": {
                "currency": item.currency,
                "product_data": {"name": item.name},
                "unit_amount": int(item.price * 100),
            },
            "quantity": 1,
        }
        for item in items
    ]

    if any(item.currency != currency for item in items):
        raise ValueError("All items must have the same currency")

    return line_items


def create_stripe_checkout_session(order: Optional[Order], line_items: List[Dict]) -> Dict:
    """Создает платежную сессию в Stripe для товара или заказа."""
    if not line_items:
        raise ValueError("No items provided for checkout session")

    try:
        currency = line_items[0]["price_data"]["currency"]

        stripe_key = settings.STRIPE_SECRET_KEYS.get(currency)
        if not stripe_key:
            raise ValueError(f"No Stripe key configured for currency: {currency}")

        stripe.api_key = stripe_key

        # Создаём скидку, если передан заказ
        discounts = []
        if order and order.discount:
            coupon = stripe.Coupon.create(
                name=order.discount.name,
                amount_off=int(order.discount.amount * 100),
                currency=currency,
                duration="once"
            )
            discounts.append({"coupon": coupon.id})

        # Создаём налог, если передан заказ
        tax_rates = []
        if order and order.tax:
            tax = stripe.TaxRate.create(
                display_name=order.tax.name,
                percentage=float(order.tax.percentage),
                inclusive=False
            )
            tax_rates.append(tax.id)

        for item in line_items:
            item["tax_rates"] = tax_rates  # Добавляем налог к каждому товару

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            discounts=discounts
        )
        return {"session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return {"error": str(e)}

