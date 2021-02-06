from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import generics, views
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from .permissions import (IsOwnerOrReadOnly, IsOwner)
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_202_ACCEPTED, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes, permission_classes
from django.http import JsonResponse
from .models import Pictureself
from .models import Like
from features.models import Feature
from variants.models import Variant
from customizations.models import Customization
import logging	#logger = logging.getLogger(__name__) #logger.error(str(request.data))
import json
from django.db.models import Q
from django.db.models import Count
from datetime import date, timedelta
from collections import Counter

from .serializers import (
    PictureselfDetailSerializer,
    PictureselfDisplaySerializer,
    PictureselfListSerializer,
)

class PictureselfDetailAPIView(generics.RetrieveAPIView):
    queryset = Pictureself.objects.all()
    serializer_class = PictureselfDetailSerializer
    permission_classes = [IsOwner]
	
class PictureselfDisplayAPIView(generics.RetrieveAPIView):
    queryset = Pictureself.objects.all()
    serializer_class = PictureselfDisplaySerializer
    permission_classes = [AllowAny]
	
class PictureselfSearchListAPIView(generics.ListAPIView):
    serializer_class = PictureselfListSerializer
    permission_classes = [AllowAny]	
    def get_queryset(self):
        query=self.kwargs['q']	
        queryset = Pictureself.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(tags__icontains=query) |
            Q(user__username__icontains=query) | 
            Q(user__profile__name__icontains=query))			
        return queryset

class PictureselfsIndexListAPIView(generics.ListAPIView):
    serializer_class = PictureselfListSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        QUERYSET_LENGTH = 55
        TIME_INTERVAL_DAYS = 10		
        end_date = date.today()	
        start_date = end_date - timedelta(days=TIME_INTERVAL_DAYS)
        end_date = end_date + timedelta(days=1)		
        queryset = (Pictureself.objects
            .annotate(like_count=Count('likes', filter=Q(likes__timestamp__range=[start_date,end_date])))
            .order_by('like_count').reverse()[:QUERYSET_LENGTH])
        return queryset
	

@api_view(['POST'])
@parser_classes((MultiPartParser, FormParser,))
@permission_classes([IsAuthenticated])
def pictureself_create(request):
	if "image" in request.data:
		new_pictureself = Pictureself(title=request.data['title'], user=request.user,
			description=request.data['description'], tags=request.data['tags'], image=request.data['image'])
		new_pictureself.save()
		return Response({"new_pictureself_id": new_pictureself.id}, status=status.HTTP_201_CREATED)
		
	feature_order = json.loads(request.data['feature_order'])
	variant_order = json.loads(request.data['variant_order'])
	features = json.loads(request.data['features'])
	created_variant_ids = json.loads(request.data['created_variant_ids'])
	
	new_pictureself = Pictureself(title=request.data['title'], user=request.user,
		description=request.data['description'], tags=request.data['tags'])
	new_pictureself.save()
		
	# add created and included features
	# if included and not overriden import variants  
	for feature_id in feature_order:

		# included; else - new
		if feature_id.isdigit():
			included_feature = Feature.objects.get(id=int(feature_id))
			# check if variants are imported
			if variant_order[feature_order.index(feature_id)] == []:
				original_pictureself = included_feature.pictureselfs.last()
				variants_to_import = original_pictureself.get_variant_ids()[original_pictureself.get_feature_ids().index(int(feature_id))]
				variant_order[feature_order.index(feature_id)] = variants_to_import

		# create new and update id in new_feature_order			
		else:
			new_feature = Feature(title=features[feature_id])
			new_feature.save()
			new_feature.pictureselfs.add(new_pictureself)
			new_feature.save()
			feature_order[feature_order.index(feature_id)] = new_feature.id
	
	int_ids_feature_order = [int(x) for x in feature_order]
	int_ids_variant_order = []

	for variant_order_line in variant_order:
		int_ids_variant_order.append([int(x) for x in variant_order_line])
		
	new_pictureself.set_feature_ids_json(int_ids_feature_order)
	new_pictureself.set_variant_ids_json(int_ids_variant_order)
	new_pictureself.save()
	
			
	for feature_id in feature_order:
		feature = Feature.objects.get(id = feature_id)
		feature.pictureselfs.add(new_pictureself)
		feature.save()
		
	return Response({"new_pictureself_id": new_pictureself.id}, status=status.HTTP_201_CREATED)

# to do: consider moving to variants.views as update_variants_chunk	
# workaround for Heroku worker timeout error
# updates chunk of variants with new file
# if result is positive client removes ids from its edited_created_variant_ids list
# and then updates next chunk till list is empty
@api_view(['PUT'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def pictureself_edit_edit_variants_chunk(request, pk):
	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	if pictureself.user != request.user:
		return Response(status=status.HTTP_403_FORBIDDEN)
	
	for edited_variant_id, edited_variant_file in request.data:
		try:
			variant = Variant.objects.get(id=int(edited_variant_id))
		except Variant.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		variant.image=edited_variant_file
		variant.save()
		
	return Response(status=status.HTTP_202_ACCEPTED)
	

# to do: consider moving to variants.views as edit_variants_chunk		
# despite containing "pictureself_edit" it's used to create new pictureself as well
@api_view(['PUT'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def pictureself_edit_create_variants_chunk(request):
	legit_created_variant_ids = {}
	for created_variant_id, created_variant_file in request.data:
		new_variant = Variant(channel=request.user, image=created_variant_file)
		new_variant.save()
		legit_created_variant_ids[created_variant_id] = (new_variant.id)
		
	context = {
		"legit_created_variant_ids": legit_created_variant_ids 
	}
	return Response(context)
	
@api_view(['PUT'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def pictureself_edit(request, pk):
	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	if pictureself.user != request.user:
		return Response(status=status.HTTP_403_FORBIDDEN)
	
	pictureself.title = request.data['title']
	pictureself.description = request.data['description']
	pictureself.tags = request.data['tags']	
	
	#non customizable
	if "image" in request.data:
		#was customizable
		if not pictureself.image:
			delete_related_data(pictureself)
			pictureself.feature_ids_json = None
			pictureself.variant_ids_json = None
			pictureself.save()
		if 	request.data['image'] != "null":
			pictureself.image=request.data['image']
		pictureself.save()
		return Response(status=status.HTTP_202_ACCEPTED)
	
	#customizable
	
	#was non customizable
	if pictureself.image:
		pictureself.image.delete()
		pictureself.image_original_name = None
		feature_order = []
		variant_order = []
	else:
		feature_order = pictureself.get_feature_ids()
		variant_order = pictureself.get_variant_ids()
	
	new_feature_order = json.loads(request.data['feature_order'])
	new_variant_order = json.loads(request.data['variant_order'])
	features = json.loads(request.data['features'])
	
	created_variant_ids = json.loads(request.data['created_variant_ids'])
	
	#delete removed variants
	new_variant_order_items = []
	for variant_order_line in new_variant_order:
		for variant_id in variant_order_line:
			new_variant_order_items.append(variant_id)
	for variant_order_line in variant_order:
		for variant_id in variant_order_line:
			if not str(variant_id) in new_variant_order_items:
				used = False
				channel_pictureselfs = pictureself.user.pictureselfs.all()
				channel_pictureselfs_len = channel_pictureselfs.count()
				i = 0
				str_repr = []
				str_repr.append("["+str(variant_id)+",")
				str_repr.append(", "+str(variant_id)+",")
				str_repr.append(", "+str(variant_id)+"]")
				str_repr.append("["+str(variant_id)+"]")
				while i < channel_pictureselfs_len and not used:
					if any(substring in channel_pictureselfs[i].variant_ids_json for substring in str_repr):
						used = True
					i += 1
				if not used:
					Variant.objects.get(id=variant_id).delete()
	
	variant_order = new_variant_order

	
	#update features with changed title
	for feature_id in feature_order:
		feature = Feature.objects.get(id=feature_id)
		if str(feature_id) in new_feature_order:
			if feature.title!=features[str(feature_id)]:
				feature.title = features[str(feature_id)]
				feature.save()
			
	#delete removed features that are not used anywhere else
	#delete records from customizations
	for feature_id in feature_order:
		if not str(feature_id) in new_feature_order:
				feature = Feature.objects.get(id=feature_id)
				if feature.pictureselfs.count()==1:
					feature.delete()
					customizations = Customization.objects.filter(channel_user=request.user)
					for customization in customizations:
						customization.delete_position(feature)
				else:
					feature.pictureselfs.remove(pictureself)
			
	#add created and included features; import variants if included and []
	for feature_id in new_feature_order:

		# already in the list or included; else - new
		if feature_id.isdigit():
		
			# if True then included; if False - it was already in list and has been update above
			if not int(feature_id) in feature_order:
				included_feature = Feature.objects.get(id=int(feature_id))
				# check if variants are imported
				if new_variant_order[new_feature_order.index(feature_id)] == []:
					original_pictureself = included_feature.pictureselfs.last()
					variants_to_import = original_pictureself.get_variant_ids()[original_pictureself.get_feature_ids().index(int(feature_id))]
					new_variant_order[new_feature_order.index(feature_id)] = variants_to_import
				#after importing variants to avoid collision with feature.pictureselfs.first()
				included_feature.pictureselfs.add(pictureself)	
				included_feature.save()
		# create new and update id in new_feature_order			
		else:
			new_feature = Feature(title=features[feature_id])
			new_feature.save()
			new_feature.pictureselfs.add(pictureself)
			new_feature.save()
			new_feature_order[new_feature_order.index(feature_id)] = new_feature.id


	int_ids_new_feature_order = [int(x) for x in new_feature_order]
	int_ids_new_variant_order = []
	for new_variant_order_line in new_variant_order:
		int_ids_new_variant_order.append([int(x) for x in new_variant_order_line])
	pictureself.set_feature_ids_json(int_ids_new_feature_order)
	pictureself.set_variant_ids_json(int_ids_new_variant_order)
	pictureself.save()
	
	return Response(status=status.HTTP_202_ACCEPTED)
		

@api_view(['DELETE'])
@permission_classes([IsOwner])
def pictureself_delete(request, pk):
	pictureself = Pictureself.objects.get(id=pk)
	
	if pictureself.user != request.user:
		return Response(status=status.HTTP_403_FORBIDDEN)
	
	#non customizable
	if pictureself.image:
		pictureself.image.delete()
		pictureself.delete()
		return Response(status=status.HTTP_200_OK)
	
	#customizable
	delete_related_data(pictureself)
	pictureself.delete()
	return Response(status=status.HTTP_200_OK)

def delete_related_data(pictureself):
	feature_order = pictureself.get_feature_ids()
	variant_order = pictureself.get_variant_ids()
	
	for feature_id, variant_line in zip(feature_order, variant_order):
		feature = Feature.objects.get(id=feature_id)
		feature.pictureselfs.remove(pictureself)
		# check if variants are imported - else delete
		if feature.pictureselfs.count() > 1:
			for variant_id in variant_line:
				used = False
				channel_pictureselfs = pictureself.user.pictureselfs.all()
				channel_pictureselfs_len = channel_pictureselfs.count()
				i = 0
				while i < channel_pictureselfs_len and not used:
					str_repr = " "+str(variant_id)+","
					if str_repr in channel_pictureselfs[i].variant_ids_json:
						used = True
					i += 1
				if not used:
					Variant.objects.get(id=variant_id).delete()
					
		# delete feature that's only used in p being deleted	
		# delete records from customizations
		else:
			customizations = Customization.objects.filter(channel_user=pictureself.user)
			for customization in customizations:
				customization.delete_position(feature)
			feature.delete()
			for variant_id in variant_line:
				Variant.objects.get(id=variant_id).delete()
	
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pictureself_features_to_include(request, pk):
	features_to_include = {}
	channel_features = Feature.objects.filter(pictureselfs__in=request.user.pictureselfs.all()).distinct()

	try:
		pictureself = Pictureself.objects.get(id=pk)
		if pictureself.user != request.user:
			return Response(status=status.HTTP_403_FORBIDDEN)
		for feature in channel_features:
			if not pictureself == feature.pictureselfs.first():
				features_to_include[str(feature.id)] = feature.title
	except Pictureself.DoesNotExist:
		for feature in channel_features:
			features_to_include[str(feature.id)] = feature.title
	
	return Response(features_to_include)
	
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def toggle_like(request, pk):

	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	try:
		like = Like.objects.get(user=request.user, pictureself=pictureself)
		like.delete()
	except Like.DoesNotExist:
		like = Like(user=request.user, pictureself=pictureself)
		like.save()

	return Response(status=status.HTTP_200_OK)
	
@api_view(['GET'])
@permission_classes([AllowAny])
def pictureself_customization_variants(request, pk):
	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	if request.query_params:
		variants = 	pictureself.get_variants_external_customization(request.query_params.dict())
	else:
		variants = pictureself.get_variants_customization(request.user)
	variant_image_urls = []
	variant_original_names = []
	for variant in variants:
		variant_image_urls.append(variant.image.url)
		variant_original_names.append(variant.original_name)	
	context = {
		"variant_image_urls": variant_image_urls,
		"variant_original_names": variant_original_names
	}
	return Response(context)

@api_view(['GET'])
@permission_classes([AllowAny])
def pictureself_feature_variants(request, pk, feature_id):
	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	
	pictureself_feature_ids = pictureself.get_feature_ids()	
	feature_index = pictureself_feature_ids.index(feature_id)
	variants = pictureself.get_variants_i(feature_index)
	variant_image_urls = []
	variant_original_names = []
	for variant in variants:
		variant_image_urls.append(variant.image.url)
		variant_original_names.append(variant.original_name)	
	context = {
		"variant_image_urls": variant_image_urls,
		"variant_original_names": variant_original_names
	}
	return Response(context)