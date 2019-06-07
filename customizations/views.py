from django.shortcuts import render
from rest_framework import generics, views
from .models import Customization
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework.decorators import api_view, permission_classes
from .permissions import (IsOwnerOrReadOnly, IsOwner)
from features.models import Feature
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework import status
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_customization(request, feature_id):
	new_position = request.data['position']
	try:
		feature = Feature.objects.get(id=feature_id)
	except Feature.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	try:
		customization = Customization.objects.get(user=request.user, channel_user=feature.pictureselfs.all()[0].user)
	except Customization.DoesNotExist:
		customization = Customization(user=request.user, channel_user=feature.pictureselfs.all()[0].user)
	
	customization.set_position(feature.id, new_position)
	customization.save()
	
	return Response(status=status.HTTP_200_OK)
