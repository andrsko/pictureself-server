from django.db import models
from django.contrib.auth.models import User
from features.models import Feature
from variants.models import Variant
from customizations.models import Customization
from django.db.models import Case, When
from PIL import Image
import base64
import uuid
from io import BytesIO
from django.conf import settings
from django.core.files.base import ContentFile
import json
import logging
import os

def get_file_path(instance, filename):
	instance.image_original_name = filename
	file_name, file_ext = os.path.splitext(filename)
	# new filename format: "test_4274B9D4-9084-441C-9617-EAD03CC9F47F.jpg"
	filename = "{0}_{1}{2}".format(file_name, uuid.uuid4(), file_ext)
	# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
	user_id = instance.user.id
	return os.path.join('user_{0}'.format(user_id), filename)
	
class Pictureself(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='pictureselfs')
	title = models.CharField(max_length=200)
	description = models.TextField(max_length=1000, null=True, blank=True)
	view_count = models.IntegerField(default=0)
	
	image = models.ImageField(upload_to=get_file_path, null=True)
	image_original_name = models.CharField(max_length=200, null=True)
	
	# JSON-serialized (text) versions of arrays
	# 	variants(ragged array) implemented as list of lists
	# 	each nested list contains variant ids that are pictureself-specific implementation features
	# 	elements in both lists are arranged: for features to represent sequence of layers, for variants to 
	# 		get one by index corresponding to customization parameter that represents index
	# 	implemented as lists for convenient work with insert and delete operations
	
	feature_ids_json = models.TextField(default="[]", null=True) 	
	variant_ids_json = models.TextField(default="[]", null=True)
	
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)
	edited_at = models.DateTimeField(auto_now_add = False, auto_now = True)
	
	def __str__(self):	
		return self.title
	
	def get_k(self):
		profile = Profile.objects.get(user=self.user)
		k = profile.get_index_of(self.id)
		return k
		
	#for use in templates: 'data:image/jpeg;base64...'
	def get_image_format(self):
		variant = self.get_variant(0, 0)
		dot_ext = os.path.splitext(variant.original_name)[1]
		ext = dot_ext[1:]
		if ext == "jpg":
			return "JPEG"
		return ext
		
	def is_customizable(self):
		if self.image:
			return False
		variant_ids = self.get_variant_ids()
		is_customizable = False
		i = 0
		while i<len(variant_ids) and not is_customizable:
			if len(variant_ids[i])>1:
				is_customizable = True
			i += 1
		return is_customizable
			
	def get_edit_title_url(self):
		return reverse('edit-picture-title', args=[str(self.id)])
		
	def get_variant_ids(self):
		jsonDec = json.decoder.JSONDecoder()
		return jsonDec.decode(self.variant_ids_json)

	def get_variant_ids_i(self, i):
		jsonDec = json.decoder.JSONDecoder()
		variant_ids = jsonDec.decode(self.variant_ids_json)
		return variant_ids[i]
	
	def get_feature_ids(self):
		jsonDec = json.decoder.JSONDecoder()
		return jsonDec.decode(self.feature_ids_json)	
	
	def get_number_of_features(self):
		feature_ids = self.get_feature_ids()
		return len(feature_ids)
		
	def set_variant_ids_json(self, variant_ids):
		self.variant_ids_json = json.dumps(variant_ids)	
	
	def set_feature_ids_json(self, feature_ids):
		self.feature_ids_json = json.dumps(feature_ids)	
	
	def get_features(self):
		feature_ids = self.get_feature_ids()
		preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(feature_ids)])
		return Feature.objects.filter(pk__in=feature_ids).order_by(preserved)
		
	def get_feature(self, i):
		feature_ids = self.get_feature_ids()
		return Feature.objects.get(pk=feature_ids[i])	
	
	def get_feature_length(self, i):
		variant_ids = self.get_variant_ids()
		return len(variant_ids[i])
	
	def get_variant(self, i, j):
		variant_ids = self.get_variant_ids()
		variant = Variant.objects.get(pk=variant_ids[i][j])
		return variant
		
	def get_variants_i(self, i):
		variant_ids = self.get_variant_ids()
		i_variant_ids = variant_ids[i]
		variants = []
		for variant_id in i_variant_ids:
			variants.append(Variant.objects.get(pk=variant_id))
		return variants
	
	def get_variants(self):
		variant_ids = self.get_variant_ids()
		variants = []
		for i_variant_ids in variant_ids:
			for variant_id in i_variant_ids:
				variants.append(Variant.objects.get(pk=variant_id))
		return variants	
		
	def get_variants_customization(self, user):
		variant_ids = self.get_variant_ids()
		feature_ids = self.get_feature_ids()
		customization_variant_ids = []
		
		try:
			customization = Customization.objects.get(user=user, channel_user=self.user)	
			customization_positions = customization.get_positions()
			
			for i_variant_ids, feature_id in zip(variant_ids, feature_ids):
				if len(i_variant_ids) >= 1:
					if str(feature_id) in customization_positions:
						if customization_positions[str(feature_id)] < len(i_variant_ids):
							customization_variant_ids.append(i_variant_ids[customization_positions[str(feature_id)]])
							
						# customized variant has been deleted	
						else:
							customization_variant_ids.append(i_variant_ids[0])
							
					# feature isn't customized yet
					else:
						customization_variant_ids.append(i_variant_ids[0])
		
		# customization does not exist or user is anonymous
		except (Customization.DoesNotExist, TypeError) as e:
			for i_variant_ids in variant_ids:
				if len(i_variant_ids) >= 1:
					customization_variant_ids.append(i_variant_ids[0])
			
		variants = []
		for variant_id in customization_variant_ids:
			variants.append(Variant.objects.get(pk=variant_id))
		return variants
		
	def add_feature(self, feature):
		feature_ids = self.get_feature_ids()
		feature_ids.append([feature.pk])
		self.set_feature_ids_json(feature_ids)
		variant_ids = self.get_variant_ids()
		variant_ids.append([])
		self.set_variant_ids_json(variant_ids)
		
	def insert_feature(self, feature, i):	
		feature_ids = self.get_feature_ids()
		feature_ids.insert(i-1,[feature.pk])
		self.set_feature_ids_json(feature_ids)
		variant_ids = self.get_variant_ids()
		variant_ids.insert(i, [])
		self.set_variant_ids_json(variant_ids)
		
	def delete_feature(self, i):
		feature_ids = self.get_feature_ids()
		Feature.objects.get(pk=feature_ids[i]).delete()
		variant_ids = self.get_variant_ids()
		i_variant_ids = variant_ids[i]
		for variant_id in i_variant_ids:
			Variants.objects.get(pk=variant_id).delete()
		del feature_ids[i]
		del variant_ids[i]
		self.set_feature_ids_json(feature_ids)
		self.set_variant_ids_json(variant_ids)
	
	def remove_feature(self, i):
		feature_ids = self.get_feature_ids()
		del feature_ids[i]
		self.set_feature_ids_json(feature_ids)
		variant_ids = self.get_variant_ids()
		i_variant_ids = variant_ids[i]
		for variant_id in i_variant_ids:
			Variants.objects.get(pk=variant_id).delete()
		del variant_ids[i]
		self.set_variant_ids_json(variant_ids)
	
	def get_variant(self, i, j):
		variant_ids = self.get_variant_ids()
		return Variant.objects.get(pk=variant_ids[i][j])
	
	def add_variant(self, i, variant):
		variant_ids = self.get_variant_ids()
		variant_ids[i].append(variant.pk)
		self.set_variant_ids_json(variant_ids)
	
	def insert_variant(self, i, j, variant):
		variant_ids = self.get_variant_ids()
		variant_ids[i].insert(j, variant.pk)
		self.set_variant_ids_json(variant_ids)
	
	def delete_variant(self, i, j):
		variant_ids = self.get_variant_ids()
		Variant.objects.get(pk=variant_ids[i][j]).delete()
		del variant_ids[i][j]
		self.set_variant_ids_json(variant_ids)
	
	def get_max_width_height(self, variants):
		widths = []
		heights = []
		for variant in variants:
			widths.append(variant.image.width)
			heights.append(variant.image.height)
		return [max(widths), max(heights)]

	def get_max_widths_heights(self, variants, i, i_variants):
		max_widths_heights = []
		widths = []
		heights = []
		for variant in variants:
			widths.append(variant.image.width)
			heights.append(variant.image.height)
		for i_variant in i_variants:
			widths[i] = i_variant.image.width
			heights[i] = i_variant.image.height
			max_widths_heights.append([max(widths), max(heights)])
		return max_widths_heights
		
	# ? test "quality" parameter in save
	def get_encoding(self, user):
		variants = self.get_variants_customization(user)
		
		max_width, max_height = self.get_max_width_height(variants)
			
		images = []
		for variant in variants:
			images.append(Image.open(variant.image))
		if len(images) > 0:
			mode = images[0].mode
			
		# to enable alpha-channel for transparency
		# ? process all formats properly: 
		# ? https://pillow.readthedocs.io/en/5.1.x/reference/Image.html#examples 
		# ? https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html#png
		# ? "Image.new(mode, (max_width, max_height), (0,0,0,0))" replaced by "Image.new("RGBA", (max_width, max_height), (0,0,0,0))" as
		# ? "result_image = Image.new(mode, (max_width, max_height), (0,0,0,0))" when "P" mode is not working:
		# ? error: "function takes exactly 1 argument (4 given)"
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			result_image = Image.new("RGBA", (max_width, max_height), (0,0,0,0))
		elif mode=="RGB":
			result_image = Image.new(mode, (max_width, max_height), "white")
		else:
			result_image = Image.new(mode, (max_width, max_height))
			
		# third argument in paste is for mask
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			for image in images:
				
				# ? workaround; see error comments above
				image = image.convert("RGBA")
				
				result_image.paste(image, (0,0), image)
		else:
			for image in images:
				result_image.paste(image, (0,0))
				
		result_io = BytesIO()
		result_image.save(result_io, format=self.get_image_format(), quality=95)
		result = base64.b64encode(result_io.getvalue()).decode('utf-8')
		
		self.view_count = self.view_count + 1
		
		return result

	def get_data_specific_variant(self, user, feature_id, variant_index):
		variants = self.get_variants_customization(user)
		variant_ids = self.get_variant_ids()
		feature_ids = self.get_feature_ids()
		feature_indices = [i for i, x in enumerate(feature_ids) if x == feature_id]
		for feature_index in feature_indices:
			variants[feature_index] = Variant.objects.get(id=variant_ids[feature_index][variant_index])
		max_width, max_height = self.get_max_width_height(variants)
		
		images = []
		for variant in variants:
			images.append(Image.open(variant.image))
		if len(images) > 0:
			mode = images[0].mode
			
		# to enable alpha-channel for transparency
		# ? process all formats properly: 
		# ? https://pillow.readthedocs.io/en/5.1.x/reference/Image.html#examples 
		# ? https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html#png
		# ? "Image.new(mode, (max_width, max_height), (0,0,0,0))" replaced by "Image.new("RGBA", (max_width, max_height), (0,0,0,0))" as
		# ? "result_image = Image.new(mode, (max_width, max_height), (0,0,0,0))" when "P" mode is not working:
		# ? error: "function takes exactly 1 argument (4 given)"
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			result_image = Image.new("RGBA", (max_width, max_height), (0,0,0,0))
		elif mode=="RGB":
			result_image = Image.new(mode, (max_width, max_height), "white")
		else:
			result_image = Image.new(mode, (max_width, max_height))
			
		# third argument in paste is for mask
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			for image in images:
				
				# ? workaround; see error comments above
				image = image.convert("RGBA")
				
				result_image.paste(image, (0,0), image)
		else:
			for image in images:
				result_image.paste(image, (0,0))
				
		result_io = BytesIO()
		result_image.save(result_io, format=self.get_image_format(), quality=95)
		result = base64.b64encode(result_io.getvalue()).decode('utf-8')
		
		self.view_count = self.view_count + 1
		
		alt = Variant.objects.get(id=variant_ids[feature_indices[0]][variant_index]).original_name	
		return [result, [max_width, max_height], alt]
		
	def get_encodings_widths_heights(self, user, i):
		variants = self.get_variants_customization(user)
		i_variants = self.get_variants_i(i)
		max_widths_heights = self.get_max_widths_heights(variants, i, i_variants)
		
		images = []
		for variant in variants:
			images.append(Image.open(variant.image))
			
		i_images = []
		for i_variant in i_variants:
			i_images.append(Image.open(i_variant.image))
			
		if len(images) > 0:
			mode = images[0].mode
			
		result_images = []
		
		# to enable alpha-channel for transparency
		if mode=='RGBA' or mode=="P" or mode=='1' or mode=='L':
			for j in range(len(i_images)):
				result_images.append(Image.new("RGBA", (max_widths_heights[j][0], max_widths_heights[j][1]), (0,0,0,0)))
		elif mode=="RGB":
			for j in range(len(i_images)):
				result_images.append(Image.new(mode, (max_widths_heights[j][0], max_widths_heights[j][1]), "white"))
		else:
			for j in range(len(i_images)):
				result_images.append(Image.new(mode, (max_widths_heights[j][0], max_widths_heights[j][1])))		
		
	
		# third argument in paste is for mask
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			for k in range(len(i_images)):
				for image in images:
					if images.index(image) == i:
					
						# ? workaround; see error comments above in get_encoding
						k_image_rgba = i_images[k].convert("RGBA")

						result_images[k].paste(k_image_rgba, (0,0), k_image_rgba)			
					else:
					
						# ? workaround; see error comments above in get_encoding
						image = image.convert("RGBA")
						
						result_images[k].paste(image, (0,0), image)
		else:
			for k in range(len(i_images)):
				for image in images:
					if images.index(image) == i:
						result_images[k].paste(i_images[k], (0,0))			
					else:
						result_images[k].paste(image, (0,0))
						
		results = []
		for result_image in result_images:
			result_io = BytesIO()
			result_image.save(result_io, format=self.get_image_format(), quality=95)
			results.append(base64.b64encode(result_io.getvalue()).decode('utf-8'))
		
		return [results, max_widths_heights]
	
	# ! refactor
	def get_encodings_widths_heights_chunk(self, user, i, start_position, number_of_options):
		variants = self.get_variants_customization(user)
		i_variants = self.get_variants_i(i)
		max_widths_heights = self.get_max_widths_heights(variants, i, i_variants)
		
		images = []
		for variant in variants:
			images.append(Image.open(variant.image))
			
		i_images = []
		for i_variant in i_variants:
			i_images.append(Image.open(i_variant.image))
			
		if len(images) > 0:
			mode = images[0].mode
			
		result_images = []
		
		# to enable alpha-channel for transparency
		if mode=='RGBA' or mode=="P" or mode=='1' or mode=='L':
			for j in range(len(i_images)):
				result_images.append(Image.new("RGBA", (max_widths_heights[j][0], max_widths_heights[j][1]), (0,0,0,0)))
		elif mode=="RGB":
			for j in range(len(i_images)):
				result_images.append(Image.new(mode, (max_widths_heights[j][0], max_widths_heights[j][1]), "white"))
		else:
			for j in range(len(i_images)):
				result_images.append(Image.new(mode, (max_widths_heights[j][0], max_widths_heights[j][1])))		
		
	
		# third argument in paste is for mask
		if mode=='1' or mode=='L' or mode=='RGBA' or mode=="P":
			for k in range(len(i_images)):
				for image in images:
					if images.index(image) == i:
					
						# ? workaround; see error comments above in get_encoding
						k_image_rgba = i_images[k].convert("RGBA")

						result_images[k].paste(k_image_rgba, (0,0), k_image_rgba)			
					else:
					
						# ? workaround; see error comments above in get_encoding
						image = image.convert("RGBA")
						
						result_images[k].paste(image, (0,0), image)
		else:
			for k in range(len(i_images)):
				for image in images:
					if images.index(image) == i:
						result_images[k].paste(i_images[k], (0,0))			
					else:
						result_images[k].paste(image, (0,0))
						
		results = []
		for result_image in result_images:
			result_io = BytesIO()
			result_image.save(result_io, format=self.get_image_format(), quality=95)
			results.append(base64.b64encode(result_io.getvalue()).decode('utf-8'))
		
		return [results[start_position:start_position+number_of_options], max_widths_heights[start_position:start_position+number_of_options]]

	# ??? in development
	# to enable multiply included in the same pictureself feature
	# example: blue circle background in avataaars: it consists of two parts: white arc and blue circle
	# that locate on different layers
	# -> ??? different row lengths
	#def get_encodings_widths_heights_feature_id(self, user, feature_id):
		#variants = self.get_variants_customization(user)
	 	#feaure_indices =[i for i, x in enumerate(self.get_feature_ids()) if x == feature_id]
		# ? alter class method feature_variants = self.get_variants(feature_id)
		# ? alter class method max_widths_heights = self.get_max_widths_heights(variants, feature_id, feature_variants)
		
		#images = []
		#for variant in variants:
			#images.append(Image.open(variant.image.path))
		#feature_images = []
		#for line in feature_variants:
			#feature_images.append([])
			#for feature_variant in line:
				#feature_images[len(feature_images)-1].append(Image.open(feature_variant.image.path))
		#if len(images) > 0:
			#mode = images[0].mode
			
		#result_images = []
		
		# create new blank images - for pictureself options	
		#if mode=='RGBA': # to enable alpha-channel for transparency
			#for i in range(len(feature_images)):
				#result_images.append(Image.new(mode, (max_widths_heights[i][0], max_widths_heights[i][1]), (0,0,0,0)))
		#else:
			#for i in range(len(i_images)):
				#result_images.append(Image.new(mode, (max_widths_heights[i][0], max_widths_heights[i][1]), "white"))
		
		# paste already customized variants for each feature that is being customized variant: 
		# 										          feature_id_c_variant_k_1							    feature_id_c_variant_s_1
		#												     		  ...											    	...
		# feature_id_1_variant | feature_id_2_variant ... feature_id_c_variant_k_j ... feature_id_g_variant ... feature_id_c_variant_s_j ...
		# 												    		  ...													...
		#if mode=='1' or mode=='L' or mode=='RGBA':
			
			# -> ??? multiply included feature different row lengths
				
			#for i_image in i_images:
				#for image in images:
					#if images.index(image) == i:
						#result_images[i_images.index(i_image)].paste(i_image, (0,0), i_image) # third argument in paste is for mask	
					#else:
						#result_images[i_images.index(i_image)].paste(image, (0,0), image) # third argument in paste is for mask
		#else:
			#for i_image in i_images:
				#for image in images:
					#if images.index(image) == i:
						#result_images[i_images.index(i_image)].paste(i_image, (0,0))			
					#else:
						#result_images[i_images.index(i_image)].paste(image, (0,0))
						
		#result_io = BytesIO()
		#results = []
		#for result_image in result_images:
			#result_image.save(result_io, format=self.get_image_format(), quality=95)
			#results.append(base64.b64encode(result_io.getvalue()).decode('utf-8'))
			
		#return [results, max_widths_heights]
		
	class Meta:
		ordering = ["-timestamp"]
	
class Like(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='likes')
	pictureself = models.ForeignKey(Pictureself, on_delete=models.CASCADE, null=True, related_name='likes')
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)
	
	class Meta:
		ordering = ["-timestamp"]