from django.conf.urls import url
from django.urls import include, path
from django.contrib import admin

from .views import (
    UserCreateAPIView,
    UserLoginAPIView,
    UserLogoutAPIView,
    UserDetailAPIView,
    UserListAPIView,
    ChannelListAPIView,
    UserDeleteAPIView,
    UserUpdateAPIView,
    UserPictureselfListAPIView,
    UserLikedPictureselfListAPIView,
    UserChannelSubscribedToListAPIView,	
	avatar_update,
	toggle_subscription,
)

urlpatterns = [
    path('', UserListAPIView.as_view(), name='user-list'),
    path('channels/', ChannelListAPIView.as_view(), name='channel-list'),
    path('register/', UserCreateAPIView.as_view(), name='user-register'),
    path('login/', UserLoginAPIView.as_view(), name='user-login'),
    path('logout/', UserLogoutAPIView.as_view(), name='user-logout'),
    path('avatar/edit/', avatar_update, name='avatar-update'),
    path('liked-pictureselfs/', UserLikedPictureselfListAPIView.as_view(), name='user-liked-pictureselfs'),	
    path('channels-subscribed-to/', UserChannelSubscribedToListAPIView.as_view(), name='channels-subscribed-to'),		
    path('<slug:username>/edit/', UserUpdateAPIView.as_view(), name='user-update'),
    path('<slug:username>/delete/', UserDeleteAPIView.as_view(), name='user-delete'),
    path('<slug:username>/pictureselfs/', UserPictureselfListAPIView.as_view(), name='user-pictureselfs'),
    path('<slug:username>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('<slug:username>/toggle-subscription/', toggle_subscription, name='toggle-subscription'),

]