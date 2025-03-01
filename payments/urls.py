from django.urls import path
from .views import CreateCheckoutSessionView, ItemDetailView

urlpatterns = [
    path('buy/<int:item_id>/', CreateCheckoutSessionView.as_view(), name='buy'),
    path("item/<int:pk>/", ItemDetailView.as_view(), name="item_detail"),
]
