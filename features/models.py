from django.db import models

class Feature(models.Model):
	title = models.CharField(max_length=200, null=False)
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)	

	#all pictureselfs it's used in; "original" pictureself (for variants to import) = the earliest one
	pictureselfs = models.ManyToManyField('pictureselfs.Pictureself', related_name='features')
	
	def __str__(self):	
		return self.title