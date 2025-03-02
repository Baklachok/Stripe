from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    CreateOrderCheckoutSessionView,
    AddToOrderView,
    ItemDetailView,
    SuccessView,
    CancelView,
)

urlpatterns = [
    path('buy/<int:item_id>/', CreateCheckoutSessionView.as_view(), name='buy'),
    path('order/add/', AddToOrderView.as_view(), name='add_to_order'),
    path('order/<int:order_id>/buy/', CreateOrderCheckoutSessionView.as_view(), name='buy_order'),
    path("item/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", CancelView.as_view(), name="cancel"),
]
