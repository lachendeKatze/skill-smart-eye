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

# NLP/NLG related libraries
from random import *
from pattern.en import parse, Sentence, article

__author__ = 'GregV', '@lachendeKatze'

LOGGER = getLogger(__name__)

class SmartEyeSkill(MycroftSkill):
    def __init__(self):
        super(SmartEyeSkill, self).__init__(name="SmartEyeSkill")
	self.camera = picamera.PiCamera() 
	self.camera.resolution = (2592,1944)

    def initialize(self):
	self.load_data_files(dirname(__file__))
	self.clarifai_app = ClarifaiApp(api_key=self.settings["api_key"])
	LOGGER.info("api_key:" + self.settings["api_key"])	

        local_image_intent = IntentBuilder("LocalImageIntent").require("LocalImageKeyword").require("FileName").build()
        self.register_intent(local_image_intent, self.handle_local_image_intent)

	general_eye_intent = IntentBuilder("GeneralEyeIntent").require("GeneralEyeKeyword").build()
	self.register_intent(general_eye_intent, self.handle_general_eye_intent)       

	describe_intent = IntentBuilder("DescribeIntent").require("DescribeKeyword").build()
	self.register_intent(describe_intent, self.handle_describe_intent)

	recognize_intent = IntentBuilder("RecognizeIntent").require("RecognizeKeyword").require("ObjName").build()
	self.register_intent(recognize_intent, self.handle_recognize_intent)

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
	self.take_picture()
	results = self.general_model_results()
	if results != "blank":
		self.speak_dialog("general.eye.results",{"results": results})
	else:
		self.speak("sorry for some reason I can't see anything")
	n,a = self.nouns_and_adjectives(results)
	LOGGER.info('results: '+ results)
	LOGGER.info('nouns: ' + ', '.join(n))
	LOGGER.info('adjectives: ' + ', '.join(a))
    
    def handle_describe_intent(self,message):
	sentence_fragment = ''
	self.speak_dialog("general.eye")
	self.take_picture()
	results = self.general_model_results()
	if results != "blank":
		sentence_fragment = self. make_description(results)
		if sentence_fragment == "blank":
			self.speak("sorry, can't seem to see anything here")
		else:
			self.speak_dialog("describe.eye.results", {"results": sentence_fragment})
	else:
		self.speak("sorry for some reason I can't see anything")

    def handle_recognize_intent(self,message):	
	self.speak_dialog("general.eye")
	object_name = message.data.get("ObjName")
	self.take_picture()
        results = self.general_model_results()
	nouns, adjectives = self.nouns_and_adjectives(results)
	if adjectives: adjective_to_use = ''.join(sample(adjectives,1))
	if object_name in nouns:
		yes_str = "Yes I see " + article(object_name) + " " + object_name
		self.speak(yes_str)
	else:
		speak_str = "no I don't see " + article(object_name) + " " + object_name
		noun_to_use = ''.join(sample(nouns,1))
                speak_str = speak_str + " but I do see " + article(noun_to_use) + " " + noun_to_use
		self.speak(speak_str)

    def take_picture(self):
	self.camera.zoom = (0.0,0.0,0.75,0.75)
	self.camera.start_preview()
	time.sleep(2)
	self.camera.stop_preview()
	self.camera.capture(self.settings["img_location"])
    
    def general_model_results(self):
	general_model = self.clarifai_app.models.get("general-v1.3")
	try:
		response = general_model.predict_by_filename(self.settings["img_location"],min_value=0.90)	
		j_dump = json.dumps(response['outputs'][0],separators=(',',': '),indent=3)
		j_load = json.loads(j_dump)
		index = 0
		results = ""
		for each in j_load['data']['concepts']:
			results = results + j_load['data']['concepts'][index]['name'] + " "
			index = index + 1
		results = results.replace('no person','') #no persn results will cause too much trouble later on
		return results
	except:
		return "blank"	

    def nouns_and_adjectives(self,results):
        nouns = []
        adjectives = []	
        results_tree = parse(results,chunks=False)
        sentence = Sentence(results_tree)
        for word in sentence:
		if word.type == 'NN':
			nouns.append(word.string)
		elif word.type =='JJ':
			adjectives.append(word.string)
        return nouns, adjectives

    def make_description(self,results):
	noun_to_use = ''
	adjective_to_use = ''

	nouns, adjectives = self.nouns_and_adjectives(results)

	if len(nouns)>=1:
		noun_to_use = ''.join(sample(nouns,1))
	else:
		return "blank"
	if len(adjectives)>=1:
		adjective_to_use = ''.join(sample(adjectives,1))
   		return article(adjective_to_use) + ' ' + adjective_to_use + ' ' + noun_to_use
	else:
		return article(noun_to_use) + ' ' + noun_to_use
	
    def stop(self):
        pass


def create_skill():
    return SmartEyeSkill()
