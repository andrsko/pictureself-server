from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics, views
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_202_ACCEPTED, HTTP_201_CREATED
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from pictureselfs.models import Pictureself
from .models import Feature

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def channel_features(request, username):

	try:
		channel = User.objects.get(username=username)
	except User.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	
	features = Feature.objects.filter(pictureselfs__in=channel.pictureselfs.all()).distinct()
	feature_ids = []
	feature_titles = []
	all_feature_ids = []	
	for feature in features:
		all_feature_ids.append(feature.id)
		pictureself = feature.pictureselfs.all()[0]
		pictureself_feature_ids = pictureself.get_feature_ids()
		pictureself_variant_ids = pictureself.get_variant_ids()
		if len(pictureself_variant_ids[pictureself_feature_ids.index(feature.id)])>1:
			feature_ids.append(feature.id)
			feature_titles.append(feature.title)

	context = {
		"feature_ids": feature_ids,
		"feature_titles": feature_titles,
		'all_feature_ids': pictureself_feature_ids		
	}
	return Response(context)
	
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pictureself_features(request, pictureself_id):

	try:
		pictureself = Pictureself.objects.get(id=pictureself_id)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	
	feature_ids = []			
	feature_titles = []
	
	pictureself_feature_ids = pictureself.get_feature_ids()
	pictureself_variant_ids = pictureself.get_variant_ids()
	for i in range(len(pictureself_feature_ids)):
		if len(pictureself_variant_ids[i])>1:
			feature_ids.append(pictureself_feature_ids[i])
			feature_titles.append(Feature.objects.get(id=pictureself_feature_ids[i]).title)

	context = {
		'feature_ids': feature_ids, 
		'feature_titles': feature_titles,
		'all_feature_ids': pictureself_feature_ids
	}
	return Response(context)