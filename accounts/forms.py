from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms import EmailInput, PasswordInput, TextInput
from django.utils.translation import gettext_lazy as _

class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}))
    first_name = forms.CharField(max_length=30, widget=TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}))
    last_name = forms.CharField(max_length=30, widget=TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': TextInput(attrs={'class': 'form-control', 'placeholder': _('Username')}),
            'password1': PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}),
            'password2': PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Repeat Password')}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'class': 'form-control', 'placeholder': _('Username or email')}))
    password = forms.CharField(widget=PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')}))

    def clean_username(self):
        identifier = self.cleaned_data['username'].strip()
        from django.contrib.auth.models import User

        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user.username
        user = User.objects.filter(username__iexact=identifier).first()
        return user.username if user else identifier
