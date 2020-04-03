from django.conf.urls import url
from django.urls import include, path

from .views import (
    customization_edit,
    customization_position	
)

urlpatterns = [	
    path('<int:feature_id>/edit/', customization_edit, name='customization-edit'),	
    path('<int:feature_id>/', customization_position, name='customization-position'),
	
]