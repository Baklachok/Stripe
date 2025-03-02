from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    CreateOrderCheckoutSessionView,
    AddToOrderView,
    ItemDetailView,
    SuccessView,
    CancelView, RemoveFromOrderView,
)

urlpatterns = [
    path('buy/<int:item_id>/', CreateCheckoutSessionView.as_view(), name='buy'),
    path('order/add/', AddToOrderView.as_view(), name='add_to_order'),
    path("order/buy/", CreateOrderCheckoutSessionView.as_view(), name="order_buy"),
    path("order/remove/", RemoveFromOrderView.as_view(), name="remove_from_order"),
    path("item/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
    path("success/", SuccessView.as_view(), name="success"),
    path("cancel/", CancelView.as_view(), name="cancel"),
]
