#!/usr/bin/env python
import sys
import random
import mylogging
from gitagent_single.msg import *
import time
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class Core:
	def __init__(self, willingness, ID, battery, sensors, actuators, motors):
		#willingness - [theta, delta]
		self.willingness = willingness

		#start always in idle
		self.state = 0

		#agent name (unique -- it has to uniquely point to some agent)
		self.ID = ID

		#Battery levels
		self.battery = battery

		#3 arrays which keep the states for sensors, actuators, motors
		self.sensors = sum(sensors)
		self.actuators = sum(actuators)
		self.motors = sum(motors)
		self.sensmot = sum([self.sensors, self.actuators, self.motors])

		#This is the minimum value for the battery levels in which it could be 
		#considered that the agent works properly
		self.battery_min = 300
		self.sensmot_min = 300

		#This could be an array, in which each element represents health over some dimension
		self.check_health()

		print self.willingness
		print self.state
		print self.battery

	#This function can perform some 'health' analysis on the state of different parts of the system.
	def check_health(self):
		if self.battery <= self.battery_min or self.sensmot <= self.sensmot_min:
			#Levels not acceptable ---> change state to dead
			self.state = 4

	def battery_change(self, change):
		self.battery = self.battery + change
	
	#It might be possible to introduce random issues here, i.e. aggravate the change of 'health'
	def sensory_motor_state_mockup(self):
		self.sensmot = sum([self.sensors, self.actuators, self.motors])

	def create_message(self, raw_content, tipmsg):
		message = Protocol_Msg()
		message.performative = 'broadcast'
		message.sender = str(self.ID)
		message.rank = 10
		message.receiver = 'all'
		message.language = 'shqip'
		message.ontology = 'shenanigans'
		message.urgency = 'INFO'
		message.content = self.create_msg_content(raw_content, tipmsg)
		message.timestamp = time.strftime('%X', time.gmtime())
		#print message
		return message

	def create_msg_content(self, raw_content, tipmsg):
		content = ''
		if tipmsg == 'position':
			for x in raw_content:
				content = content + str(x) + '|'
		else:
			for x in raw_content:
				content = content + str(x[0]) + '|'
		return content

	def willing2ask(self, inputs):
		#Define some parameters
		hmin = 400
		hmax = 4500
		hdiff = 10

		unitmin = 0
		unitmax = 1
		unitdiff = 0.1

		#Define antecedents (inputs): holds variables and membership functions
		#Health represents an aggregation of the values for battery, sensor, actuator and motor condition
		health = ctrl.Antecedent(np.arange(hmin, hmax, hdiff), 'health')

		#Best known agent to ask, in which helpfulness and success rate are combined beforehand, using a dot product
		best_agent = ctrl.Antecedent(np.arange(unitmin, unitmax, unitdiff), 'best_agent')

		#The environment represents a combined value of the danger associated with physical obstacles, and the general culture of the population
		#as in the case of the best known agent, these can be combined using a dot product
		environment = ctrl.Antecedent(np.arange(unitmin, unitmax, unitdiff), 'environment')

		#Agent abilities and resources needed in the scope of one task could also be combined in order to be represented by one fuzzy input
		abil_res = ctrl.Antecedent(np.arange(unitmin, unitmax, unitdiff), 'abil_res')
		abil_res['some'] = fuzz.trapmf(abil_res.universe, [0.0, 0.0, 0.4, 0.4])
		abil_res['all_&optional'] = fuzz.trapmf(abil_res.universe, [0.6, 0.6, 1.0, 1.0])
		#abil_res.view()
		#The agent's own progress wrt to tasks, or plans in general could also serve as a trigger to interact or not
		own_progress = ctrl.Antecedent(np.arange(unitmin, unitmax, unitdiff), 'own_progress')

		#Fuzzy output, the willingness to ask for help
		willingness = ctrl.Consequent(np.arange(unitmin, unitmax, unitdiff), 'willingness')

		#Auto membership function population
		health.automf(3)
		best_agent.automf(3)
		environment.automf(3)
		own_progress.automf(3)
		willingness.automf(3)

		#health.view()
		#willingness.view()

		#Define rules
		rules = []

		## either poor health or only some of abilities and resources are enough to have high willingness to ask for help
		rules.append(ctrl.Rule(health['poor'] | abil_res['some'] | own_progress['poor'], willingness['good']))
		rules.append(ctrl.Rule((health['good'] | health['average']) & abil_res['all_&optional'] & (own_progress['good'] | own_progress['average']), willingness['poor']))
		#rules.append(ctrl.Rule(best_agent['good'] & health['average'] & abil_res['all_&optional'], willingness['average']))
		#rules.append(ctrl.Rule(best_agent['poor'] & health['average'] & abil_res['all_&optional'], willingness['poor']))

		## View rules graphically
		#rule1.view()

		#inputs = [4400, 0.7, 0.3, 0.5]

		interact_ctrl = ctrl.ControlSystem(rules)
		interact = ctrl.ControlSystemSimulation(interact_ctrl)
		interact.input['health'] = inputs[0]
		#interact.input['best_agent'] = inputs[1]
		interact.input['abil_res'] = inputs[2]
		interact.input['own_progress'] = inputs[3]

		interact.compute()

		print interact.output['willingness']
		test = random.random()
		print test
		#The function will return depend either true or false, either ask or don't ask for help
		if test < interact.output['willingness']:
			return True
		else:
			return False
