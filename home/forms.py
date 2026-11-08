from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["full_name", "email", "phone_number", "message"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "cr-form-control",
                    "placeholder": "نام و نام خانوادگی *",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "cr-form-control",
                    "placeholder": "پست الکترونیک (اختیاری)",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "cr-form-control",
                    "placeholder": "تلفن همراه (مثلاً 09123456789) *",
                    "maxlength": "11",
                    "dir": "ltr",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "cr-form-control",
                    "id": "exampleFormControlTextarea1",
                    "rows": "4",
                    "placeholder": "متن پیام شما *",
                }
            ),
        }