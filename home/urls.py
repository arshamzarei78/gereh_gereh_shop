from django.urls import path
from . import views

app_name = "home"

urlpatterns = [

    path('',views.HomeView.as_view(),name='home'),
    path('faq',views.FaqView.as_view(),name='faq'),
    path("contact_us/", views.ContactUsView.as_view(), name="contact_us"),
]