from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

# دیکشنری ترجمه قطعی نام ماه‌ها (برای سرورهایی که لوکال فارسی ندارند)
MONTHS_FA = {
    'Farvardin': 'فروردین', 'farvardin': 'فروردین',
    'Ordibehesht': 'اردیبهشت', 'ordibehesht': 'اردیبهشت',
    'Khordad': 'خرداد', 'khordad': 'خرداد',
    'Tir': 'تیر', 'tir': 'تیر',
    'Mordad': 'مرداد', 'mordad': 'مرداد',
    'Shahrivar': 'شهریور', 'shahrivar': 'شهریور',
    'Mehr': 'مهر', 'mehr': 'مهر',
    'Aban': 'آبان', 'aban': 'آبان',
    'Azar': 'آذر', 'azar': 'آذر',
    'Dey': 'دی', 'dey': 'دی',
    'Bahman': 'بهمن', 'bahman': 'بهمن',
    'Esfand': 'اسفند', 'esfand': 'اسفند',
}

@register.filter(name='to_jalali')
def to_jalali(value, format_string='%Y/%m/%d'):
    if not value:
        return ""
    
    try:
        if timezone.is_aware(value):
            value = timezone.localtime(value)
            
        # تلاش برای تنظیم لوکال (اگر سیستم‌عامل پشتیبانی کند)
        try:
            jdatetime.set_locale('fa_IR')
        except:
            pass

        j_date = jdatetime.datetime.fromgregorian(datetime=value)
        formatted_date = j_date.strftime(format_string)
        
        # جایگزینی اجباری فینگیلیش با فارسی
        for eng, per in MONTHS_FA.items():
            formatted_date = formatted_date.replace(eng, per)
        
        # تبدیل اعداد به فارسی
        persian_numbers = formatted_date.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
        return formatted_date.translate(persian_numbers)
        
    except Exception:
        return value