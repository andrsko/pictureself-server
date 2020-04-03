from django.conf.urls import url
from django.urls import include, path

from .views import (
    PictureselfDetailAPIView,
    PictureselfDisplayAPIView,
    PictureselfsIndexListAPIView,
   	pictureself_edit_edit_variants_chunk,
    pictureself_edit_create_variants_chunk,
    pictureself_edit,
    pictureself_create,
    pictureself_delete,
    pictureself_features_to_include,	
	PictureselfSearchListAPIView,	
	toggle_like,
	pictureself_customization_variants,
	pictureself_feature_variants
)

urlpatterns = [
    path('index/', PictureselfsIndexListAPIView.as_view(), name='pictureselfs-index'),
    path('search/<str:q>/', PictureselfSearchListAPIView.as_view(), name='pictureselfs-search'), 		
    path('<int:pk>/', PictureselfDisplayAPIView.as_view(), name='pictureself-display'),
    path('<int:pk>/data/', PictureselfDetailAPIView.as_view(), name='pictureself-data'),
    path('<int:pk>/toggle-like/', toggle_like, name='pictureself-toggle-like'),
    path('<int:pk>/features-to-include/', pictureself_features_to_include, name='pictureself-features-to-include'),
    path('<int:pk>/edit-edit-variants-chunk/', pictureself_edit_edit_variants_chunk, name='pictureself-edit-edit-variants-chunk'),
    path('edit-create-variants-chunk/', pictureself_edit_create_variants_chunk, name='pictureself-edit-create-variants-chunk'),
    path('0/edit/', pictureself_create, name='pictureself-create'),
    path('<int:pk>/edit/', pictureself_edit, name='pictureself-edit'),
    path('<int:pk>/delete/', pictureself_delete, name='pictureself-delete'),
    path('<int:pk>/customization-variants/', pictureself_customization_variants, name='pictureself-customization-variants'),
    path('<int:pk>/feature-variants/<int:feature_id>/', pictureself_feature_variants, name='pictureself-feature-variants'),
	
]