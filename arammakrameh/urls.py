
from django.contrib import admin
from django.urls import path , include,re_path
from . import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('checkout/', include('checkout.urls')),
    path('blog/', include('blog.urls', namespace='blog')),
]+ static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
