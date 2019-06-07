from django.db import models
from django.contrib.auth.models import User
import json

# ? refactor: feature as foreingKey; fields: position, timestamp		
class Customization(models.Model):
	user = models.ForeignKey(User, related_name='customizations', on_delete=models.CASCADE)	
	channel_user = models.ForeignKey(User, related_name='channel_customizations', null=True, on_delete=models.CASCADE)
	positions_json = models.TextField(default="{}", null=True)
	timestamp = models.DateTimeField(auto_now_add = True, auto_now = False)
	
	def get_positions(self):
		jsonDec = json.decoder.JSONDecoder()
		return jsonDec.decode(self.positions_json)

	def set_position(self, feature_id, position):
		jsonDec = json.decoder.JSONDecoder()
		positions = jsonDec.decode(self.positions_json)
		positions[str(feature_id)] = position
		self.positions_json = json.dumps(positions)
	
	def set_positions_json(self, positions):
		self.positions_json = json.dumps(positions)
	
	#def add_position(self, feature):
	#	positions = self.get_positions()
	#	positions[feature.id] = -1
	#	self.set_positions_json(positions)		
	
	def delete_position(self, feature):
		positions = self.get_positions()
		if str(feature.id) in positions:
			del positions[str(feature.id)]
		self.set_positions_json(positions)
