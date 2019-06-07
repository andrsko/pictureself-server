from django.conf.urls import url
from django.urls import include, path

from .views import (
    PictureselfDetailAPIView,
    PictureselfDisplayAPIView,
    PictureselfsIndexListAPIView,
    pictureself_edit,
    pictureself_create,
    pictureself_delete,
    pictureself_features_to_include,
	pictureself_options,
	original_pictureself_options,
	PictureselfSearchListAPIView,	
	toggle_like
)

urlpatterns = [
    path('index/', PictureselfsIndexListAPIView.as_view(), name='pictureselfs-index'),
    path('search/<str:q>/', PictureselfSearchListAPIView.as_view(), name='pictureselfs-search'), 		
    path('<int:pk>/options/<int:feature_id>/', pictureself_options, name='pictureself-options'),	
    path('options/<int:feature_id>/', original_pictureself_options, name='original-pictureself-options'),	
    path('<int:pk>/', PictureselfDisplayAPIView.as_view(), name='pictureself-display'),
    path('<int:pk>/data/', PictureselfDetailAPIView.as_view(), name='pictureself-data'),
    path('<int:pk>/toggle-like/', toggle_like, name='pictureself-toggle-like'),
    path('<int:pk>/features-to-include/', pictureself_features_to_include, name='pictureself-features-to-include'),
    path('0/edit/', pictureself_create, name='pictureself-create'),
    path('<int:pk>/edit/', pictureself_edit, name='pictureself-edit'),
    path('<int:pk>/delete/', pictureself_delete, name='pictureself-delete'),
	
]