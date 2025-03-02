import logging
from typing import Dict, List

import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
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


def create_stripe_checkout_session(line_items: List[Dict]) -> Dict:
    """Создает платежную сессию в Stripe."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
        )
        return {"session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return {"error": str(e)}


# ---------- Serializers ----------
class AddToOrderSerializer(serializers.Serializer):
    """Сериализатор для добавления товара в заказ."""
    item_id = serializers.IntegerField(required=True)
    order_id = serializers.CharField(required=False, allow_null=True)


# ---------- API Views ----------
class CreateCheckoutSessionView(APIView):
    """Создает сессию оплаты для одиночного товара."""

    def post(self, request, item_id: int) -> Response:
        item = get_object_or_404(Item, id=item_id)

        try:
            line_items = create_stripe_line_items([item])
            result = create_stripe_checkout_session(line_items)
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AddToOrderView(APIView):
    """Добавляет товар в существующий или новый заказ."""

    def post(self, request) -> Response:
        serializer = AddToOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item = get_object_or_404(Item, id=serializer.validated_data["item_id"])
        order_id = serializer.validated_data.get("order_id")

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id) if order_id else Order.objects.create()
                order.items.add(item)
                order.save()

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Order error: {str(e)}")
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"order_id": order.id}, status=status.HTTP_200_OK)


class CreateOrderCheckoutSessionView(APIView):
    """Создает сессию оплаты для нескольких товаров."""

    def post(self, request) -> Response:
        items_data = request.data.get("items", [])
        if not items_data:
            return Response({"error": "Order is empty"}, status=status.HTTP_400_BAD_REQUEST)

        items = Item.objects.filter(id__in=[item["id"] for item in items_data])
        if len(items) != len(items_data):
            return Response({"error": "One or more items not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            line_items = create_stripe_line_items(items)
            result = create_stripe_checkout_session(line_items)
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RemoveFromOrderView(APIView):
    """Удаляет товар из заказа."""

    def post(self, request) -> Response:
        order_id = request.data.get("order_id")
        item_id = request.data.get("item_id")

        if not order_id or not item_id:
            return Response({"error": "order_id and item_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id)
        item = get_object_or_404(Item, id=item_id)

        if item in order.items.all():
            order.items.remove(item)
            order.save()
            return Response({"message": "Item removed from order"}, status=status.HTTP_200_OK)
        return Response({"error": "Item not in order"}, status=status.HTTP_400_BAD_REQUEST)


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
