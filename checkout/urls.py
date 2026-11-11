from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    path('', views.checkout_view, name='checkout'),
    path("payment/<int:order_id>/", views.payment_request_view, name="payment"),
    path("payment/verify/", views.payment_verify_view, name="payment_verify"),
    path("track/", views.track_order_view, name="track_order"),
    path("track/<int:order_id>/", views.track_order_view, name="track_order_detail"),
]