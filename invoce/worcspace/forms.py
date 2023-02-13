from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import get_user_model, authenticate
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from .utils import send_email_for_verify
from .models import Invoice

User = get_user_model()


class MyUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'phone', 'first_name', 'last_name')
        # field_classes = {"username": UsernameField}

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Login'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Phone'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'First name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Last name'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})


class MyAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(attrs={"autofocus": True, 'class': 'form-control', 'placeholder': 'Login'}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password", 'class': 'form-control', 'placeholder': 'Password'}),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                if not self.user_cache.email_verify:
                    send_email_for_verify(self.request, self.user_cache)
                    raise ValidationError(
                        'You have not verified your email',
                        code="invalid_login",
                    )
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class InvoiceForm(ModelForm):
    for_the_company = forms.CharField(max_length=256,
                                      required=True,
                                      widget=forms.TextInput(attrs={'placeholder': 'company',
                                                                    'id': 'id_company_name',
                                                                    'class': 'form-control',
                                                                    # 'style': 'width: 100%',
                                                                    }))

    class Meta:
        model = Invoice
        fields = ['description', 'file_obj', 'email']
        labels = {
            # "description": "",
            "file_obj": ""
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'description',
                                                  'class': 'form-control',
                                                  # 'style': 'width: 100%'
                                                  }),
            'file_obj': forms.FileInput(attrs={'id': 'inputGroupFile04',
                                               'class': 'form-control',
                                               'aria - describedby': "inputGroupFile04",
                                                'aria - label': "Upload"
                                               # 'style': 'width: 100%'
                                               }),
            'email': forms.EmailInput(attrs={'placeholder': 'Email',
                                             'class': 'form-control',
                                             # 'style': 'width: 100%'

                                             }),
            # 'image': forms.ClearableFileInput(attrs={'multiple': True})
        }

    field_order = ('for_the_company', 'description', 'file_obj', 'email')


class UpdateInvoiceForm(ModelForm):
    # for_the_company = forms.CharField(max_length=256,
    #                                   required=True,
    #                                   widget=forms.TextInput(attrs={'placeholder': 'company',
    #                                                                 'id': 'id_company_name',
    #                                                                 'class': 'form-control',
    #                                                                 # 'style': 'width: 100%',
    #                                                                 }))

    def __init__(self, *args, **kwargs):
        super(UpdateInvoiceForm, self).__init__(*args, **kwargs)
        # Making location required
        self.fields['file_obj'].required = False

    class Meta:
        model = Invoice
        fields = ['description', 'file_obj', 'email']
        labels = {
            # "description": "",
            "file_obj": ""
        }
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'description',
                                                  'class': 'form-control',
                                                  # 'style': 'width: 100%'
                                                  }),
            'file_obj': forms.FileInput(attrs={'id': 'inputGroupFile04',
                                               'class': 'form-control',
                                               'aria - describedby': "inputGroupFile04",
                                                'aria - label': "Upload"
                                               # 'style': 'width: 100%'
                                               }),
            'email': forms.EmailInput(attrs={'placeholder': 'Email',
                                             'class': 'form-control',
                                             # 'style': 'width: 100%'

                                             }),
            # 'image': forms.ClearableFileInput(attrs={'multiple': True})
        }

    field_order = ('for_the_company', 'description', 'file_obj', 'email')
