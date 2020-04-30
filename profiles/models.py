from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	about = models.TextField(max_length=500, blank=True)
	name = models.CharField(max_length=32, default='', blank=True)	
	avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

	def __str__(self):
		return self.user.username
		
# New superuser profile
@receiver(post_save, sender=User)
def create_superuser_profile(sender, instance, created, **kwargs):
    if created and instance.is_superuser:	
        Profile.objects.create(user=instance)

	
# automatically create a token for each new user
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Subscription(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_subscriptions')
	channel = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='channel_subscribtions')
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)
	
	class Meta:
		ordering = ["-timestamp"]