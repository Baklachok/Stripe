from django.urls import path
from .views import CreateCheckoutSessionView

urlpatterns = [
    path('buy/<int:item_id>/', CreateCheckoutSessionView.as_view(), name='buy'),
]
