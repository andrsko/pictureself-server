from django.conf.urls import url
from django.urls import include, path

from .views import (
    channel_features,
	pictureself_features,
)


urlpatterns = [
    path('p/<int:pictureself_id>/', pictureself_features, name='pictureself-features'),
    path('<slug:username>/', channel_features, name='channel-features'),
	
]