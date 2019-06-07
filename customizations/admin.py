from django.contrib import admin
from .models import Customization

class CustomizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'channel_user'] 
	
admin.site.register(Customization, CustomizationAdmin)
