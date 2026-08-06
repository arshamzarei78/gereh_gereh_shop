from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('detail/<int:pk>/<str:slug>',views.PtoductView.as_view(),name='detail'),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
]