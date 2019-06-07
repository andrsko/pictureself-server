from django.conf.urls import url
from django.urls import include, path

from .views import (
    edit_customization
)

urlpatterns = [	
    path('<int:feature_id>/edit/', edit_customization, name='edit-customization'),	
	
]