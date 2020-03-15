from django.shortcuts import render
from rest_framework import generics, views
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly
)
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_202_ACCEPTED, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes, permission_classes
from .models import Variant
import logging	#logger = logging.getLogger(__name__) #logger.error(str(request.data))


@api_view(['PUT'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def variant_edit(request, pk):
	try:
		variant = Variant.objects.get(pk=pk)
	except Variant.DoesNotExist:
		return Response(status=status.HTTP_404_NOT_FOUND)
		
	if variant.channel != request.user:
		return Response(status=status.HTTP_403_FORBIDDEN)
	
	variant.image=request.data['file']
	variant.save()
		
	return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
@parser_classes([FormParser, MultiPartParser])
@permission_classes([IsAuthenticated])
def variant_create(request):
	logger = logging.getLogger(__name__)

	new_variant = Variant(channel=request.user, image=request.data['file'])
	new_variant.save()
	context = {
		"new_variant_id": new_variant.id
	}
	logger.error("<><><><><><><><><><"+str(new_variant.id))
	return Response(context)