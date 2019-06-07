from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework.validators import UniqueValidator
from django.contrib.humanize.templatetags.humanize import naturaltime
from profiles.models import Profile
from profiles.models import Subscription
import logging	

class UserDetailSerializer(serializers.ModelSerializer):
    about = serializers.CharField(source='profile.about')
    name = serializers.CharField(source='profile.name')
    avatar = serializers.ImageField(source='profile.avatar')
    date_joined = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    number_of_subscribers = serializers.SerializerMethodField()	
    is_customizable = serializers.SerializerMethodField()	
	
    class Meta:
        model = User
        fields = [
            'username',
            'name',
            'about',
			'avatar',
            'date_joined',
			'is_subscribed',
			'number_of_subscribers',
			'is_customizable',			
		]
        lookup_field = 'username'

    def get_date_joined(self, obj):
        return naturaltime(obj.date_joined)

    def get_is_subscribed(self, obj):
        try:
            subscription = Subscription.objects.get(user=self.context.get('request').user, channel=obj)
            return True
			
		# SubscriptionDoesNotExist or isn't authenticated		
        except:
            return False

    def get_number_of_subscribers(self, obj):
        return Subscription.objects.filter(channel=obj).count()			

    def get_is_customizable(self, obj):
        user = obj
        pictureselfs = user.pictureselfs.all()
        is_customizable = False
        i=0		
        while i<len(pictureselfs) and not is_customizable:
            if pictureselfs[i].is_customizable():
                is_customizable=True	
            i += 1				
        return is_customizable
		
class UserListSerializer(serializers.ModelSerializer):
    about = serializers.CharField(source='profile.about')
    avatar = serializers.ImageField(source='profile.avatar')	
    name = serializers.CharField(source='profile.name')
    number_of_subscribers = serializers.SerializerMethodField()		
    class Meta:
        model = User
        fields = [
            'username',
			'avatar',			
            'name',
            'about',
            'date_joined',
			'number_of_subscribers'
        ]
		
    def get_number_of_subscribers(self, obj):
        return Subscription.objects.filter(channel=obj).count()		
		
class UserUpdateSerializer(serializers.ModelSerializer):
    # A field from the user's profile:
    about = serializers.CharField(source='profile.about', allow_blank=True)
    name = serializers.CharField(
    	source='profile.name',
    	max_length=32,
    	allow_blank=True
    )
    current_password = serializers.CharField(
        write_only=True,
        allow_blank=True,
        label=_("Current Password"),
        help_text=_('Required'),
    )
    new_password = serializers.CharField(
        allow_blank=True,
        default='',
        write_only=True,
        min_length=4,
        max_length=32,
        label=_("New Password"),
    )
    email = serializers.EmailField(
        allow_blank=True,
        default='',
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='has already been taken by other user'
        )]
    )

    class Meta:
        model = User
        fields = (
            'username',
            'name',
            'email',
            'current_password',
            'new_password',
            'about',
        )
        read_only_fields = ('username',)
        lookup_field = 'username'

    def update(self, instance, validated_data):
        # make sure requesting user provide his current password
        # e.g if admin 'endiliey' is updating a user 'donaldtrump',
        # currentPassword must be 'endiliey' password instead of 'donaldtrump' password
        try:
            username = self.context.get('request').user.username
        except:
            msg = _('Must be authenticated')
            raise serializers.ValidationError(msg, code='authorization')
	
        password = validated_data.get('current_password')
        validated_data.pop('current_password', None)
		
        if not password:
            msg = _('Must provide current password')
            raise serializers.ValidationError(msg, code='authorization')
        user = User.objects.get(username=username)
        if not user.check_password(password):
            msg = _('Sorry, the password you entered is incorrect.')
            raise serializers.ValidationError(msg, code='authorization')

        # change password to a new one if it exists
        new_password = validated_data.get('new_password') or None
        if new_password:
            instance.set_password(new_password)
        validated_data.pop('new_password', None)

        # Update user profile fields
        profile_data = validated_data.pop('profile', None)
        profile = instance.profile
        for field, value in profile_data.items():
            if value:
                setattr(profile, field, value)
        # Update user fields
        for field, value in validated_data.items():
            if value:
                setattr(instance, field, value)

        profile.save()
        instance.save()
        return instance

class UserCreateSerializer(serializers.ModelSerializer):
    # A field from the user's profile:
    username = serializers.SlugField(
        min_length=4,
        max_length=32,
        help_text=_(
            'Required. 4-32 characters. Letters, numbers, underscores or hyphens only.'
        ),
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='has already been taken by other user'
        )],
        required=True
    )
    password = serializers.CharField(
        min_length=4,
        max_length=32,
        write_only=True,
        help_text=_(
            'Required. 4-32 characters.'
        ),
        required=True
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='has already been taken by other user'
        )]
    )
    about = serializers.CharField(source='profile.about', allow_blank=True, default='')
    name = serializers.CharField(
        source='profile.name',
        allow_blank=True,
        default='',
        max_length=32
    )

    class Meta:
        model = User
        fields = (
            'username',
            'name',
            'email',
            'password',
            'about',
        )

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        user = User(
                username = username,
                email = email
        )
        user.set_password(password)
        user.save()

        profile = Profile(
            user = user,
            about = profile_data.get('about', ''),
            name = profile_data.get('name', ''),
        )
        profile.save()
        return user		
		
class UserTokenSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs

class UserLoginSerializer(serializers.ModelSerializer):
    username = serializers.SlugField(
        max_length=32,
        help_text=_(
            'Required. 32 characters or fewer. Letters, numbers, underscores or hyphens only.'
        ),
        required=True
    )
    token = serializers.CharField(allow_blank=True, read_only=True)
    name = serializers.CharField(source='profile.name', read_only=True)
    class Meta:
        model = User
        fields = [
            'username',
            'name',
            'password',
            'token',
        ]
        extra_kwargs = {"password": {"write_only": True} }