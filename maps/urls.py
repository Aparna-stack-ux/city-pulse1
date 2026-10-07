from django.urls import path
from .views import city_map

urlpatterns = [
    path('', city_map, name='map'),
]
