from django.urls import path
from . import views


app_name = "accounts"

urlpatterns = [

    path('register',views.RegisterView.as_view(),name='register'),
    path("load-cities/",views.load_cities,name="load_cities"),
    path("send-otp/",views.SendOTPView.as_view(),name="send_otp"),
    path("verify-otp/",views.VerifyOTPView.as_view(),name="verify_otp"),
    
]