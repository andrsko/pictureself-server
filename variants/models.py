from django.db import models
import os
import uuid
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db.models.signals import post_delete
import logging


def get_file_path(instance, filename):
	instance.original_name = filename
	file_name, file_ext = os.path.splitext(filename)
	# new filename format: "test_4274B9D4-9084-441C-9617-EAD03CC9F47F.jpg"
	filename = "{0}_{1}{2}".format(file_name, uuid.uuid4(), file_ext)
	# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
	user_id = instance.channel.id
	return os.path.join('user_{0}'.format(user_id), filename)
	
class Variant(models.Model):
	image = models.ImageField(upload_to=get_file_path)
	original_name = models.CharField(max_length=200, null="True", blank="True")
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)
	
	# for future implementation (included feature variants synchronization)
	pictureselfs = models.ManyToManyField('pictureselfs.Pictureself', related_name='variants')
	
	# to name/detect folder file is going to
	channel = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='variants')

	
# These two auto-delete files from filesystem when they are unneeded:

@receiver(models.signals.post_delete, sender=Variant)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Variant` object is deleted.
    """
    variants_with_the_file = Variant.objects.filter(image=instance.image)
	#https://stackoverflow.com/questions/20516570/django-delete-file-from-amazon-s3
    if variants_with_the_file.count() == 0:	
        instance.image.delete(save=False)	
#    if instance.image and variants_with_the_file.count() == 0:
#        if os.path.isfile(instance.image.path):
#            os.remove(instance.image.path)

@receiver(models.signals.pre_save, sender=Variant)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `Variant` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Variant.objects.get(pk=instance.pk).image
    except Variant.DoesNotExist:
        return False
    logger = logging.getLogger(__name__)

    new_file = instance.image
    if old_file != new_file:	
        variants_with_the_file = Variant.objects.filter(image=old_file)
        for v in variants_with_the_file:
            logger.error("_______________---------->>>>>>"+str(v.original_name))
        if variants_with_the_file.count() == 1:
			#https://stackoverflow.com/questions/20516570/django-delete-file-from-amazon-s3		
            Variant.objects.get(pk=instance.pk).image.delete(save=False)			
#            if os.path.isfile(old_file.path):
#                os.remove(old_file.path)

