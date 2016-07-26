import os
import json
import logging
from datetime import datetime

from s2sphere import LatLng

from pogom import config

log = logging.getLogger(__name__)

from pb_alarm import PB_Alarm
from slack_alarm import Slack_Alarm
from twilio_alarm import Twilio_Alarm
from ..utils import get_pokemon_name

class Notifications:

	def __init__(self):
		filepath = os.path.dirname(os.path.dirname(__file__))
		with open(os.path.join(filepath, '..', 'alarms.json')) as file:
			settings = json.load(file)
			alarm_settings = settings["alarms"]
			self.notify_list = settings["pokemon"]
			self.seen = {}
			self.alarms = []
			for alarm in alarm_settings:
				if alarm['active'] == "True" :
					if alarm['type'] == 'pushbullet' :
						self.alarms.append(PB_Alarm(alarm['api_key']))
					elif alarm['type'] == 'slack' :
						self.alarms.append(Slack_Alarm(alarm['api_key'], alarm['channel']))
					elif alarm['type'] == 'twilio' :
						self.alarms.append(Twilio_Alarm(alarm['account_sid'], alarm['auth_token'], alarm['to_number'], alarm['from_number']))
					else:
						log.info("Alarm type not found: " + alarm['type'])
				else:
					log.info("Alarm not activated: " + alarm['type'])


	def notify_pkmns(self, pkmn):
		for id in pkmn:
			if id not in self.seen:
				pkinfo = {
					'name': get_pokemon_name(pkmn[id]['pokemon_id']),
					'lat': pkmn[id]['latitude'],
					'lng': pkmn[id]['longitude'],
					'disappear_time': pkmn[id]['disappear_time']
				}
				self.seen[id] = pkinfo
				if(self.notify_list[pkinfo['name']] == "True"):
					origin_point = LatLng.from_degrees(config['ORIGINAL_LATITUDE'], config['ORIGINAL_LONGITUDE'])
					pokemon_point = LatLng.from_degrees(pkinfo['lat'], pkinfo['lng'])
					pkinfo['distance'] = int(origin_point.get_distance(pokemon_point).radians * 6366468.241830914)
					diff = pokemon_point - origin_point
					diff_lat = diff.lat().degrees
					diff_lng = diff.lng().degrees
					pkinfo['direction'] = (('N' if diff_lat >= 0 else 'S') if abs(diff_lat) > 1e-4 else '') + (
						('E' if diff_lng >= 0 else 'W') if abs(diff_lng) > 1e-4 else '')
					log.info(pkinfo['name']+" notification has been triggered!")
					log.info("Encounter ID:" + str(id))
					for alarm in self.alarms:
						alarm.pokemon_alert(pkinfo)
		self.clear_stale()

	#clear stale so that the seen set doesn't get too large
	def clear_stale(self):
		old = []
		for id in self.seen:
			if self.seen[id]['disappear_time'] < datetime.utcnow() :
				old.append(id)
		for id in old:
			del self.seen[id]

	def notify_lures(self, lures):
		raise NotImplementedError("This method is not yet implimented.")

	def notify_gyms(self, gyms):
		raise NotImplementedError("This method is not yet implimented.")
