from django.contrib import admin
from .models import Feature

class FeatureAdmin(admin.ModelAdmin):
    list_display = ['id', 'title'] 
	
admin.site.register(Feature, FeatureAdmin)
