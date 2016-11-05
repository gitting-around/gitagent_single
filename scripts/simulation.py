#!/usr/bin/env python
#Parent class of agent, implementing the core parts of the theoretical concept
#Framework v1.0
import sys
import random

class Simulation0:
	def __init__(self):
		## The attributes below serve as a timestamp for each function called ######
		# handle_serve, call_serve, callback_bc, wander, adapt, run_step, fsm
		self.handle = 0
		self.call = 0
		self.callback_bc = 0
		self.idle = 0
		self.interact = 0
		self.execute = 0
		self.fsm = 0
		self.regenerate = 0
		self.dead = 0
		self.hell = 0

		#self.stdout_log = 'RESULT/pop_size.'+str(popSize) +'/prova.'+str(provaNr)+'/stdout_' + str(ID) + '_' + str(delta) +'_'+ str(depend_nr)
		#self.stdout_callback = 'RESULT/pop_size.'+str(popSize) +'/prova.'+str(provaNr)+'/stdout_callback' + str(ID) + '_' + str(delta) +'_'+ str(depend_nr)
		#self.stdout_handle = 'RESULT/pop_size.'+str(popSize) +'/prova.'+str(provaNr)+'/stdout_handle' + str(ID) + '_' + str(delta) +'_'+ str(depend_nr)

	def inc_iterationstamps(self, iteration_stamp):
		iteration_stamp = iteration_stamp + 1
		return iteration_stamp

	#trick to emulate the selection of a couple of services the agent can provide
	def select_services(self, agent_id, depend_nr): 
		try: 	#try to do it with relative paths
			filename = '/home/mfi01/catkin_ws/src/GITagent/scripts/services_list_' + str(depend_nr)
			service_file = open(filename, 'r')

			active_servs = []
			for line in service_file:
				active_servs.append([int(i) for i in line.split('	')])
			service_file.close()

			nr_srvs = len(active_servs)

	## for each agent with id, choose total_servs/2, starting from index = id ######
			indices = []
			for i in range(agent_id - 1, agent_id + nr_srvs/2 - 1):
				if i > nr_srvs - 1:
					indices.append(i%len(active_servs))
				else:
					indices.append(i)
			active_servs = [active_servs[i] for i in indices]
	################################################################################
		
	## Random way to choose services #########################################
			#remove 80% of services
			srv_remove = int(0.7 * nr_srvs)
			#for i in range(1, srv_remove + 1):
				#ind = random.randint(0, len(active_servs)-1)
				#active_servs.pop(ind)
	##########################################################################
			return active_servs
		except IOError:
			print "Error: can\'t find file or read service_list file"
