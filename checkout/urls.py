from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    path('', views.Checkout.as_view(), name='checkout'),
]