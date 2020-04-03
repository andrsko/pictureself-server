from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework.validators import UniqueValidator
from django.contrib.humanize.templatetags.humanize import naturaltime
from .models import Pictureself
from .models import Like
from features.models import Feature
from variants.models import Variant
from customizations.models import Customization
from profiles.models import Profile

# ? create separate PictureselfListSerializer

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
    username = serializers.SerializerMethodField()
	
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
            'username',
            'features',
            'variants'				
        ]
		
    def get_username(self, obj):
        pictureself = obj
        return pictureself.user.username
		
class PictureselfDisplaySerializer(serializers.ModelSerializer):
    image_urls = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()	
    avatar = serializers.ImageField(source='user.profile.avatar')
    is_customizable = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    number_of_likes = serializers.SerializerMethodField()
	
    class Meta:
        model = Pictureself
        fields = [
            'id',
            'title',
            'description',
            'view_count',
            'timestamp',
            'username',
            'name',			
			'avatar',	
            'image_urls',
			'is_customizable',
			'is_liked',
			'number_of_likes'
        ]

    def get_image_urls(self, obj):
        user = self.context.get('request').user
        pictureself = obj
        variants = pictureself.get_variants_customization(user)
        image_urls = []
        for variant in variants:
            image_urls.append(variant.image.url)			
        return image_urls
		
    def get_username(self, obj):
        pictureself = obj
        return pictureself.user.username

    def get_name(self, obj):
        pictureself = obj
        profile = Profile.objects.get(user=pictureself.user)
        return profile.name
		
    def get_is_customizable(self, obj):
        pictureself = obj
        return pictureself.is_customizable()
		
    def get_is_liked(self, obj):
        user = self.context.get('request').user
        pictureself = obj
        try:
            like = Like.objects.get(user=user, pictureself=pictureself) 
            is_liked = True
        except:
            is_liked = False
        return is_liked

    def get_number_of_likes(self, obj):
        pictureself = obj
        return Like.objects.filter(pictureself=pictureself).count()
	
class PictureselfListSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()	
    name = serializers.SerializerMethodField()		
    image_urls = serializers.SerializerMethodField()
    class Meta:
        model = Pictureself
        fields = [
            'id',
            'title',
            'username',
            'name',
            'image_urls',			
        ]
		
    def get_image_urls(self, obj):
        user = self.context.get('request').user
        pictureself = obj
        variants = pictureself.get_variants_customization(user)
        image_urls = []
        for variant in variants:
            image_urls.append(variant.image.url)			
        return image_urls
				
    def get_username(self, obj):
        pictureself = obj
        return pictureself.user.username
		
    def get_name(self, obj):
        pictureself = obj
        profile = Profile.objects.get(user=pictureself.user)
        return profile.name