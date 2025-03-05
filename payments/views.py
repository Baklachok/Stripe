import logging
from typing import Dict

import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item, Order
from .serilizers import AddToOrderSerializer
from .services import create_stripe_line_items, create_stripe_checkout_session

logger = logging.getLogger(__name__)


# ---------- API Views ----------
class RetrieveCheckoutSessionView(APIView):
    """Возвращает `session_id` для оплаты товара по его `id`."""

    renderer_classes = [JSONRenderer]

    def get(self, request, item_id: int) -> Response:
        item = get_object_or_404(Item, id=item_id)

        try:
            line_items = create_stripe_line_items([item])
            result = create_stripe_checkout_session(request,None, line_items)  # order=None, работаем только с line_items
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)


class CreateCheckoutSessionView(APIView):
    """Создает сессию оплаты для одиночного товара."""

    def post(self, request, item_id: int) -> Response:
        item = get_object_or_404(Item, id=item_id)

        try:
            line_items = create_stripe_line_items([item])
            order = Order.objects.create()  # Создаём временный заказ
            result = create_stripe_checkout_session(request, None, line_items)
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
                if order_id:
                    # Если передан order_id, добавляем товар в существующий заказ
                    order = get_object_or_404(Order, id=order_id)
                else:
                    # Если order_id нет, создаем новый заказ
                    order = Order.objects.create()

                order.items.add(item)
                order.save()

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Order error: {str(e)}")
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"order_id": order.id}, status=status.HTTP_200_OK)



class CreateOrderCheckoutSessionView(APIView):
    """Создает сессию оплаты для заказа с учетом скидки и налога."""

    def post(self, request) -> Response:
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)  # Добавлено!

        order = get_object_or_404(Order, id=order_id)

        if not order.items.exists():
            return Response({"error": "Order is empty"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            line_items = create_stripe_line_items(order.items.all())
            result = create_stripe_checkout_session(request, order, line_items)
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
    model = Item
    template_name = "item_detail.html"
    context_object_name = "item"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        currency = self.object.currency
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEYS.get(currency, "")
        return context


class SuccessView(TemplateView):
    """Страница успешной оплаты."""
    template_name = "success.html"


class CancelView(TemplateView):
    """Страница отмены оплаты."""
    template_name = "cancel.html"
