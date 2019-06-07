from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework.validators import UniqueValidator
from django.contrib.humanize.templatetags.humanize import naturaltime
from .models import Pictureself
from features.models import Feature
from variants.models import Variant

class FeatureDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=200)
    class Meta:
        model = Feature
        fields = [
            'id',
            'title'
        ]

class VariantDetailSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)
    original_name = serializers.CharField()
    class Meta:
        model = Variant
        fields = [
            'id',
            'original_name',
            'image'
        ]

class PictureselfDetailSerializer(serializers.ModelSerializer):
    features = FeatureDetailSerializer(many=True)
    variants = VariantDetailSerializer(many=True)
    class Meta:
        model = Pictureself
        fields = [
            'id',
            'title',
            'description',
            'view_count',
            'feature_ids_json',
            'variant_ids_json',
            'timestamp',
            'user',
            'features',
            'variants'				
        ]

