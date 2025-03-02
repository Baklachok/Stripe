import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Item, Order

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(line_items):
    """Создает платежную сессию в Stripe."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        return {"session_id": session.id}
    except stripe.error.StripeError as e:
        return {"error": str(e)}


class CreateCheckoutSessionView(APIView):
    """Создает сессию оплаты в Stripe для одного товара (Item)."""

    def post(self, request, item_id):
        item = get_object_or_404(Item, id=item_id)
        line_items = [{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': item.name},
                'unit_amount': int(item.price * 100),
            },
            'quantity': 1,
        }]
        result = create_stripe_session(line_items)
        status_code = status.HTTP_201_CREATED if "session_id" in result else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(result, status=status_code)


class AddToOrderView(APIView):
    """Добавляет товар в заказ (создаёт новый заказ, если его нет)."""

    def post(self, request):
        item_id = request.data.get("item_id")
        order_id = request.data.get("order_id")

        if not item_id:
            return Response({"error": "item_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        item = get_object_or_404(Item, id=item_id)

        order, created = Order.objects.get_or_create(id=order_id) if order_id else Order.objects.create()
        order.items.add(item)

        return Response({"order_id": order.id}, status=status.HTTP_200_OK)


class CreateOrderCheckoutSessionView(APIView):
    """Создаёт сессию оплаты в Stripe для заказа."""

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        if not order.items.exists():
            return Response({"error": "Order is empty"}, status=status.HTTP_400_BAD_REQUEST)

        line_items = [
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item.name},
                    'unit_amount': int(item.price * 100),
                },
                'quantity': 1,
            }
            for item in order.items.all()
        ]

        result = create_stripe_session(line_items)
        status_code = status.HTTP_201_CREATED if "session_id" in result else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(result, status=status_code)


class ItemDetailView(DetailView):
    """Детальное представление товара."""
    model = Item
    template_name = "item_detail.html"
    context_object_name = "item"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        return context


class SuccessView(TemplateView):
    """Страница успешной оплаты."""
    template_name = "success.html"


class CancelView(TemplateView):
    """Страница отмененной оплаты."""
    template_name = "cancel.html"
