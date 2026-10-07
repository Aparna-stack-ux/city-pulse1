from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = [
            'title', 'description', 'category', 'priority', 'ward_number',
            'location', 'latitude', 'longitude', 'image', 'anonymous',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Complaint Title')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Describe the issue'), 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'ward_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ward Number')}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Location')}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Latitude')}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Longitude')}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
