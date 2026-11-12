from .models import Category
from home.models import SiteSetting
def global_categories(request):
    return {
        'categories': Category.objects.all()
    }
def site_settings(request):
    return {
        "site_setting": SiteSetting.objects.first()
    }