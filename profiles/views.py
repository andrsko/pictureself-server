from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import generics, views
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)
from .permissions import IsOwnerOrReadOnly
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_202_ACCEPTED, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes, permission_classes
from django.http import JsonResponse
from pictureselfs.models import Pictureself
from pictureselfs.models import Like
from profiles.models import Subscription
from django.db.models import Case, When
from django.db.models import Count

User = get_user_model()

from .serializers import (
    UserCreateSerializer,
    UserLoginSerializer,
    UserTokenSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserUpdateSerializer,
)
from pictureselfs.serializers import (
    PictureselfListSerializer,
)

class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]

class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [AllowAny]

class UserDeleteAPIView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'username'
    permission_classes = [IsOwnerOrReadOnly]

class UserUpdateAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'username'
    permission_classes = [IsOwnerOrReadOnly]

class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [AllowAny]
	
class ChannelListAPIView(generics.ListAPIView):
    serializer_class =  UserListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        channels = User.objects.annotate(pictureself_count=Count('pictureselfs', distinct=True)).filter(pictureself_count__gte=1)
        channels_annotated = channels.annotate(channel_subscribtion_count=Count('channel_subscribtions', distinct=True))
        queryset = channels_annotated.order_by('-channel_subscribtion_count')[:55]		
        return queryset

class UserChannelSubscribedToListAPIView(generics.ListAPIView):
    serializer_class =  UserListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        subscriptions = Subscription.objects.filter(user=self.request.user)	
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(subscriptions.values_list('channel_id', flat=True))])
        channels_subscribed_to = User.objects.filter(id__in=subscriptions.values_list('channel_id', flat=True)).order_by(preserved)	
        return channels_subscribed_to
		
class UserPictureselfListAPIView(generics.ListAPIView):
    serializer_class = PictureselfListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        username = self.kwargs['username']
        return Pictureself.objects.filter(user__username=username)
		
class UserLikedPictureselfListAPIView(generics.ListAPIView):
    serializer_class = PictureselfListSerializer
    permission_classes = [IsAuthenticated]
	
    def get_queryset(self):
        likes = 	Like.objects.filter(user=self.request.user)
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(likes.values_list('pictureself_id', flat=True))])
        liked_pictureselfs = Pictureself.objects.filter(id__in=likes.values_list('pictureself_id', flat=True)).order_by(preserved)	
        return liked_pictureselfs
		
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def avatar_update(request):
    user = request.user
    profile = user.profile
    profile.avatar = request.data['file']
    profile.save()
    return Response({"avatar_url": profile.avatar.url})
	
	
class UserLoginAPIView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserTokenSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            avatar = ""
            if user.profile.avatar and hasattr(user.profile.avatar, 'url'):
                avatar = user.profile.avatar.url
            return Response({
                'token': token.key,
                'username': user.username,
                'name': user.profile.name,
				'avatar': avatar,
            }, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

class UserLogoutAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # simply delete the token in server side
            request.user.auth_token.delete()
            return Response(status=HTTP_200_OK)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)
			
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def toggle_subscription(request, username):
    try:
        channel = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
		
    try:
        subscription = Subscription.objects.get(user=request.user, channel=channel)
        subscription.delete()
    except Subscription.DoesNotExist:
        subscription = Subscription(user=request.user, channel=channel)
        subscription.save()

    return Response(status=status.HTTP_200_OK)