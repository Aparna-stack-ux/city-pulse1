from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _

class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('garbage', _('Garbage')),
        ('street_light', _('Street Light')),
        ('water', _('Water Leakage')),
        ('road', _('Road Damage')),
        ('drainage', _('Drainage')),
        ('environment', _('Environment')),
        ('traffic', _('Traffic')),
        ('electricity', _('Electricity')),
        ('public_transport', _('Public Transport')),
        ('emergency', _('Emergency')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('assigned', _('Assigned')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('rejected', _('Rejected')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=120)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    ward_number = models.CharField(max_length=10)
    location = models.CharField(max_length=180)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    image = models.ImageField(upload_to='complaint_images/', blank=True, null=True)
    anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(
    max_length=20,
    default="WEB"
    )
    phone_number = models.CharField(
    max_length=15,
    blank=True,
    null=True
)
    def __str__(self):
        return f'{self.title} ({self.category})'
