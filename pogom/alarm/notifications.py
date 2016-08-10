import os
import json
import logging

import time

from pogom import config

log = logging.getLogger(__name__)

from pb_alarm import PB_Alarm
from slack_alarm import Slack_Alarm
from twilio_alarm import Twilio_Alarm
from ..utils import get_pokemon_name
from ..utils import parse_distance
from ..utils import get_args
import googlemaps
import math

class Notifications:

	def __init__(self):
		filepath = os.path.dirname(os.path.dirname(__file__))
		with open(os.path.join(filepath, '..', 'alarms.json')) as file:
			settings = json.load(file)
			alarm_settings = settings["alarms"]
			self.notify_list = settings["pokemon"]
			self.max_distance = settings["max_distance"]
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
		args = get_args()
		self.gclient = googlemaps.Client(args.gdirections_key)

	def notify_pkmns(self, pkmn):
		if pkmn['encounter_id'] not in self.seen:
			pkmn['name'] = get_pokemon_name(pkmn['pokemon_id'])
			self.seen[pkmn['encounter_id']] = pkmn
			distance_1 = self.distance((config['latitude'], config['longitude']), (pkmn['latitude'], pkmn['longitude'])) * 1000
			if self.notify_list[pkmn['name']] == "True" or distance_1 < 105:
				distance, duration = parse_distance(self.gclient, config['latitude'], config['longitude'], pkmn['latitude'], pkmn['longitude'])
				if distance['value'] < self.max_distance:
					pkmn['distance'] = distance['text']
					pkmn['distance_duration'] = duration['text']
					log.info(pkmn['name']+" notification has been triggered!")
					log.info("Encounter ID:" + str(id))
					for alarm in self.alarms:
						alarm.pokemon_alert(pkmn)
		self.clear_stale()

	def distance(self, origin, destination):
		lat1, lon1 = origin
		lat2, lon2 = destination
		radius = 6371 # km

		dlat = math.radians(lat2-lat1)
		dlon = math.radians(lon2-lon1)
		a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
												  * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
		c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
		d = radius * c

		return d

	#clear stale so that the seen set doesn't get too large
	def clear_stale(self):
		old = []
		for id in self.seen:
			if self.seen[id]['disappear_time'] < time.time() :
				old.append(id)
		for id in old:
			del self.seen[id]

	def notify_lures(self, lures):
		raise NotImplementedError("This method is not yet implimented.")

	def notify_gyms(self, gyms):
		raise NotImplementedError("This method is not yet implimented.")
