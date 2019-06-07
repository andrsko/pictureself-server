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


from .serializers import (
    PictureselfDetailSerializer,
    PictureselfDisplaySerializer,
    PictureselfListSerializer,
)

class PictureselfDetailAPIView(generics.RetrieveAPIView):
    queryset = Pictureself.objects.all()
    serializer_class = PictureselfDetailSerializer
    permission_classes = [IsOwner]
	
# in gallery	
class PictureselfDisplayAPIView(generics.RetrieveAPIView):
    queryset = Pictureself.objects.all()
    serializer_class = PictureselfDisplaySerializer
    permission_classes = [AllowAny]
	
class PictureselfSearchListAPIView(generics.ListAPIView):
    serializer_class = PictureselfListSerializer
    permission_classes = [AllowAny]	
    def get_queryset(self):
        query=self.kwargs['q']	
        queryset = Pictureself.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
        return queryset
	
class PictureselfsIndexListAPIView(generics.ListAPIView):
    queryset = Pictureself.objects.order_by('-timestamp')[:55]
    serializer_class = PictureselfListSerializer
    permission_classes = [AllowAny]
	

@api_view(['POST'])
@parser_classes((MultiPartParser, FormParser,))
@permission_classes([IsAuthenticated])
def pictureself_create(request):
	feature_order = json.loads(request.data['feature_order'])
	variant_order = json.loads(request.data['variant_order'])
	features = json.loads(request.data['features'])
	
	new_pictureself = Pictureself(title=request.data['title'], user=request.user, description=request.data['description'])
	new_pictureself.save()
	
	#add created variants
	for variant_order_line in variant_order:
		for variant_id in variant_order_line:
			new_variant = Variant(channel=request.user, image=request.data[variant_id])
			new_variant.save()
			new_variant.pictureselfs.add(new_pictureself)
			new_variant.save()
			variant_order_line[variant_order_line.index(variant_id)] = new_variant.id
	
			
	#add created and included features; import variants if included and []
	for feature_id in feature_order:

		# included; else - new
		if feature_id.isdigit():
			included_feature = Feature.objects.get(id=int(feature_id))
			# check if variants are imported
			if variant_order[feature_order.index(feature_id)] == []:
				original_pictureself = included_feature.pictureselfs.last()
				variants_to_import_data_from = original_pictureself.get_variant_ids()[original_pictureself.get_feature_ids().index(int(feature_id))]
				variants_with_imported_data = []
				for variant_id in variants_to_import_data_from:
					variant = Variant.objects.get(id=variant_id)
					new_variant = Variant(image=variant.image, original_name=variant.original_name, channel=request.user)
					new_variant.save()
					new_variant.pictureselfs.add(new_pictureself)
					new_variant.save()
					variants_with_imported_data.append(new_variant.id)	
				variant_order[feature_order.index(feature_id)] = variants_with_imported_data

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
	
	for variant_order_line in variant_order:
		for variant_id in variant_order_line:
			variant = Variant.objects.get(id=variant_id)
			variant.pictureselfs.add(new_pictureself)
			variant.save()
	for feature_id in feature_order:
		feature = Feature.objects.get(id = feature_id)
		feature.pictureselfs.add(new_pictureself)
		feature.save()
		
	return Response({"new_pictureself_id": new_pictureself.id}, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def pictureself_edit(request, pk):

	pictureself = Pictureself.objects.get(id=pk)
	if pictureself.user != request.user:
		return Response(status=status.HTTP_403_FORBIDDEN)
	
	feature_order = pictureself.get_feature_ids()
	variant_order = pictureself.get_variant_ids()
	
	pictureself.title = request.data['title']
	pictureself.description = request.data['description']

	new_feature_order = json.loads(request.data['feature_order'])
	new_variant_order = json.loads(request.data['variant_order'])
	features = json.loads(request.data['features'])
	edited_created_variant_ids = json.loads(request.data['edited_created_variant_ids'])
				
	#update edited variants
	for variant_id in edited_created_variant_ids:
		if variant_id.isdigit():
			edited_variant=Variant.objects.get(id=int(variant_id))
			edited_variant.image=request.data[variant_id]
			edited_variant.save()
		
	#delete removed variants
	new_variant_order_items = []
	for variant_order_line in new_variant_order:
		for variant_id in variant_order_line:
			new_variant_order_items.append(variant_id)
	for variant_order_line in variant_order:
		for variant_id in variant_order_line:
			if not str(variant_id) in new_variant_order_items:
				variant = Variant.objects.get(id=variant_id)
				if variant.pictureselfs.count()==1:
					variant.delete()
				else:
					variant.pictureselfs.remove(pictureself)

	#add created variants
	variant_order_items = []
	for variant_order_line in variant_order:
		for variant_id in variant_order_line:
			variant_order_items.append(variant_id)				
	for new_variant_order_line in new_variant_order:
		for variant_id in new_variant_order_line:
			if not variant_id.isdigit():
				new_variant = Variant(channel=request.user, image=request.data[variant_id])
				new_variant.save()
				new_variant.pictureselfs.add(pictureself)
				new_variant.save()
				new_variant_order_line[new_variant_order_line.index(variant_id)] = new_variant.id
	
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
					variants_to_import_data_from = original_pictureself.get_variant_ids()[original_pictureself.get_feature_ids().index(int(feature_id))]
					variants_with_imported_data = []
					for variant_id in variants_to_import_data_from:
						variant = Variant.objects.get(id=variant_id)
						new_variant = Variant(image=variant.image, original_name=variant.original_name, channel=request.user)
						new_variant.save()
						new_variant.pictureselfs.add(pictureself)
						new_variant.save()
						variants_with_imported_data.append(new_variant.id)	
					new_variant_order[new_feature_order.index(feature_id)] = variants_with_imported_data
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
		
	feature_order = pictureself.get_feature_ids()
	variant_order = pictureself.get_variant_ids()
	
	for feature_id, variant_line in zip(feature_order, variant_order):
		feature = Feature.objects.get(id=feature_id)
		# check if variants are imported - else delete
		if feature.pictureselfs.count() > 1:
			variants_are_imported = False
			for feature_pictureself in feature.pictureselfs.all():
				feature_index = feature_pictureself.get_feature_ids().index(feature_id)
				if feature_pictureself.get_variant_ids()[feature_index] == variant_line:
					variants_are_imported = True			
			if not variants_are_imported:
				for variant_id in variant_line:
					Variant.objects.get(id=variant_id).delete()
		# delete feature that's only used in p being deleted	
		# delete records from customizations
		else:
			customizations = Customization.objects.filter(channel_user=request.user)
			for customization in customizations:
				customization.delete_position(feature)
			feature.delete()
			for variant_id in variant_line:
				Variant.objects.get(id=variant_id).delete()

	pictureself.delete()
	return Response(status=status.HTTP_200_OK)
	
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
def pictureself_options(request, pk, feature_id):

	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	try:
		feature = Feature.objects.get(id=feature_id)
	except Feature.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	
	try:
		customization = Customization.objects.get(user=request.user, channel_user=pictureself.user)
	except Customization.DoesNotExist:
		customization = Customization(user=request.user, channel_user=pictureself.user)
		customization.save()
		
	customization_positions = customization.get_positions()
	if str(feature_id) in customization_positions:
		active_option_index = customization_positions[str(feature_id)]
	else: 
		active_option_index = -1
	
	pictureself_feature_ids = pictureself.get_feature_ids()
	i = pictureself_feature_ids.index(feature_id)
	encodings, widths_heights = pictureself.get_encodings_widths_heights(request.user, i)
	ext = pictureself.get_image_format()
	alts = []
	variants_i = pictureself.get_variants_i(i)
	for variant_i in variants_i:
		alts.append(variant_i.original_name)
	context = {
		"encodings": encodings,
		"widths_heights": widths_heights,
		"active_option_index": active_option_index, 
		"ext": ext, 
		"alts":alts 
	}
	return Response(context)
	
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def original_pictureself_options(request, feature_id):

	try:
		feature = Feature.objects.get(id=feature_id)
	except Feature.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
	
	if feature.pictureselfs.all().count()==0:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	pictureself = feature.pictureselfs.all()[0]
	
	try:
		customization = Customization.objects.get(user=request.user, channel_user=pictureself.user)
	except Customization.DoesNotExist:
		customization = Customization(user=request.user, channel_user=pictureself.user)
		customization.save()
		
	customization_positions = customization.get_positions()
	if str(feature_id) in customization_positions:
		active_option_index = customization_positions[str(feature_id)]
	else: 
		active_option_index = -1
	
	pictureself_feature_ids = pictureself.get_feature_ids()
	i = pictureself_feature_ids.index(feature_id)	
	encodings, widths_heights = pictureself.get_encodings_widths_heights(request.user, i)
	ext = pictureself.get_image_format()
	alts = []
	variants_i = pictureself.get_variants_i(i)
	for variant_i in variants_i:
		alts.append(variant_i.original_name)
	context = {
		"encodings": encodings,
		"widths_heights": widths_heights,
		"active_option_index": active_option_index, 
		"ext": ext, 
		"alts":alts 
	}
	return Response(context)
	
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def toggle_like(request, pk):

	try:
		pictureself = Pictureself.objects.get(pk=pk)
	except Pictureself.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	try:
		like = Like.objects.get(pictureself=pictureself)
		like.delete()
	except Like.DoesNotExist:
		like = Like(user=request.user, pictureself=pictureself)
		like.save()

	return Response(status=status.HTTP_200_OK)