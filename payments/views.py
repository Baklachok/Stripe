import logging
from typing import Dict, List

import stripe
from django.conf import settings
from django.db import transaction
from django.views.generic import DetailView, TemplateView
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item, Order

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------- Service functions ----------
def create_stripe_line_items(items: List[Item]) -> List[Dict]:
    """Создает список элементов для платежной сессии Stripe."""
    if not items:
        raise ValueError("Items list is empty")

    currency = items[0].currency
    line_items = []

    for item in items:
        if item.currency != currency:
            raise ValueError("All items must have the same currency")

        line_items.append({
            'price_data': {
                'currency': currency,
                'product_data': {'name': item.name},
                'unit_amount': int(item.price * 100),
            },
            'quantity': 1,
        })

    return line_items


def create_stripe_checkout_session(line_items: List[Dict]) -> Dict:
    """Создает платежную сессию в Stripe."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        return {'session_id': session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return {'error': str(e)}


# ---------- Serializers ----------
class AddToOrderSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в заказ."""
    item_id = serializers.IntegerField(required=True)
    order_id = serializers.CharField(required=False, allow_null=True)


# ---------- API Views ----------
class CreateCheckoutSessionView(APIView):
    """Создает сессию оплаты для одиночного товара."""

    def post(self, request, item_id: int) -> Response:
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise NotFound(detail="Item not found")

        try:
            line_items = create_stripe_line_items([item])
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result = create_stripe_checkout_session(line_items)
        return Response(result,
                        status=status.HTTP_201_CREATED if 'session_id' in result else status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddToOrderView(APIView):
    """Добавляет товар в существующий или новый заказ."""

    def post(self, request) -> Response:
        serializer = AddToOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        item_id = data['item_id']
        order_id = data.get('order_id')

        # Получение товара
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            raise NotFound(detail="Item not found")

        # Работа с заказом
        try:
            with transaction.atomic():
                if order_id:
                    order = Order.objects.select_for_update().get(id=order_id)
                else:
                    order = Order.objects.create()

                order.items.add(item)
                order.save()

        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Order error: {str(e)}")
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'order_id': order.id}, status=status.HTTP_200_OK)


class CreateOrderCheckoutSessionView(APIView):
    """Создает сессию оплаты для заказа."""

    def post(self, request, order_id: str) -> Response:
        try:
            order = Order.objects.prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist:
            raise NotFound(detail="Order not found")
        except (ValueError, ValidationError):
            return Response({'error': 'Invalid order ID'}, status=status.HTTP_400_BAD_REQUEST)

        if not order.items.exists():
            return Response({'error': 'Order is empty'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            line_items = create_stripe_line_items(order.items.all())
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result = create_stripe_checkout_session(line_items)
        return Response(result,
                        status=status.HTTP_201_CREATED if 'session_id' in result else status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------- Template Views ----------
class ItemDetailView(DetailView):
    """Детальное отображение товара с интеграцией Stripe."""
    model = Item
    template_name = "item_detail.html"
    context_object_name = "item"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        return context


class SuccessView(TemplateView):
    """Страница успешной оплаты."""
    template_name = "success.html"


class CancelView(TemplateView):
    """Страница отмены оплаты."""
    template_name = "cancel.html"