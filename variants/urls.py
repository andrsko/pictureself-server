from django.conf.urls import url
from django.urls import include, path

from .views import (
	variant_edit,
	variant_create
)

urlpatterns = [
    path('create/', variant_create, name='variant-create'),
    path('<int:pk>/edit/', variant_edit, name='variant-edit'),
]