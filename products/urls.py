from django.urls import path
from . import views


app_name = 'products'

urlpatterns = [
    path('detail/<int:pk>/<str:slug>',views.PtoductView.as_view(),name='detail'),
    
]