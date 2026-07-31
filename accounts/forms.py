from django import forms
from .models import User , Address
from iranian_cities.models import City
from django.core.validators import RegexValidator

class RegisterForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "email",
        )
        widgets ={
            'first_name':forms.TextInput(attrs={
                'class':'cr-form-control',
                'placeholder':"نام خود را وارد نمایید",
                
            }),

            'last_name':forms.TextInput(attrs={
                'class':'cr-form-control',
                'placeholder':"نام خانوادگی خود را وارد کنید",
            }),

            'email':forms.EmailInput(attrs={
                'class':'cr-form-control',
                'placeholder':"ایمیل خود را وارد کنید",
            }),
            
            'phone_number':forms.NumberInput(attrs={
                "class":"cr-form-control bg-light",
                'placeholder':"شماره تلفن خود را وارد کنید",
                'readonly':True
            })
        }

class AddressForm(forms.ModelForm):

    class Meta:
        model = Address

        exclude = (
            "user",
            "is_default",
            "address_name",
            "created_at",
        )

        widgets = {


            "province": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "province"
                }
            ),

            "city": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "city"
                }
            ),

            "postal_code": forms.TextInput(
                attrs={
                    "class": "cr-form-control"
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "cr-form-control",
                    "rows": 4
                }
            ),


        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["city"].queryset = City.objects.none()

        if "province" in self.data:
            try:
                province_id = int(
                    self.data.get("province")
                )

                self.fields["city"].queryset = (
                    City.objects.filter(
                        province_id=province_id
                    ).order_by("name")
                )

            except (ValueError, TypeError):
                pass

class VerifyOTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "cr-form-control",
                "placeholder": "کد تایید"
            }
        )
    )

class SendOTPForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="شماره موبایل معتبر نیست."
            )
        ]
    )