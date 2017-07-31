# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

# Mycroft libraries
from os.path import dirname
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger

# clarifai libraries
from clarifai import rest
from clarifai.rest import ClarifaiApp 
from clarifai.rest import Image as ClImage

#required libraries
import time
import json
import picamera

__author__ = 'GregV', '@lachendeKatze'

LOGGER = getLogger(__name__)

class SmartEyeSkill(MycroftSkill):
    def __init__(self):
        super(SmartEyeSkill, self).__init__(name="SmartEyeSkill")
	self.clarifai_app = ClarifaiApp(api_key='***Your API Key Here')
 
	self.camera = picamera.PiCamera() 
	self.camera.resolution = (2592,1944)

    def initialize(self):
	self.load_data_files(dirname(__file__))

        local_image_intent = IntentBuilder("LocalImageIntent").require("LocalImageKeyword").require("FileName").build()
        self.register_intent(local_image_intent, self.handle_local_image_intent)

	general_eye_intent = IntentBuilder("GeneralEyeIntent").require("GeneralEyeKeyword").build()
	self.register_intent(general_eye_intent, self.handle_general_eye_intent)       

    def handle_local_image_intent(self, message):

	fileName = message.data.get("FileName")
	general_model = self.clarifai_app.models.get("general-v1.3")
	image_file = '/opt/mycroft/skills/skill-smart-eye/TestImages/' + fileName + '.jpg'

	try:
	        response = general_model.predict_by_filename(image_file,min_value=0.98)
		j_dump = json.dumps(response['outputs'][0],separators=(',',': '),indent=3)
		j_load = json.loads(j_dump)
		index = 0
		result_string = ""
		for each in j_load['data']['concepts']:
			result_string = result_string + j_load['data']['concepts'][index]['name'] + " "
			index = index + 1
		self.speak_dialog("local.image.results")
	except:
		result_string = "I can't find " + fileName + " sorry"
	
	self.speak(result_string)
	
    def handle_general_eye_intent(self,message):
	self.speak_dialog("general.eye")
	# 1st task is take a picture with the PiCamera and for now put it in
	# in a standard location and get it a standard file name; this will
	# result in an overwrite everytime, but ok to test functionality
	# TODO: give memory! rename time&date stamp each image?, perhaps restamp with time date and 
	# dominate concepts from clarifai?
	# TODO: learn about mycrfot config to allow for storing image in a flexible location
	
	image_location = '/home/mycroft/smarteye.jpg'		
	self.camera.zoom = (0.0,0.0,0.75,0.75)
	self.camera.start_preview()
	time.sleep(2)
	self.camera.stop_preview()
	self.camera.capture(image_location)
		
	# send the image to clarifai for analysis with the 'general" model and
	# return concepts with 98% or greater confidence
	general_model = self.clarifai_app.models.get("general-v1.3")
	try:
		response = general_model.predict_by_filename(image_location,min_value=0.90)	
		j_dump = json.dumps(response['outputs'][0],separators=(',',': '),indent=3)
		j_load = json.loads(j_dump)
		index = 0
		results = ""
		for each in j_load['data']['concepts']:
			results = results + j_load['data']['concepts'][index]['name'] + " "
			index = index + 1
		self.speak_dialog("general.eye.results",{"results": results})
	except:
		self.speak("sorry for some reason I can't see anything")

    def stop(self):
        pass


def create_skill():
    return SmartEyeSkill()
