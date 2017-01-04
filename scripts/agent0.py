#!/usr/bin/env python
# Parent class of agent, implementing the core parts of the theoretical concept
# Framework v1.0
import sys
import time
import mylogging
import core_aboutme
import knowledge
import simulation
import rospy
from gitagent_single.msg import *
from gitagent_single.srv import *
from threading import Lock
import random
import timeit


class Agent0:
    def __init__(self, ID, conf, services, willingness, simulation, popSize, provaNr, depend_nr, battery, sensors,
                 actuators, motors):

        # logging class
        self.log = mylogging.Logging(popSize, provaNr, ID, willingness[1], depend_nr)

        self.start_time = timeit.default_timer()
        self.end_time = 180

        # They will contain arrays of topic's names ###
        self.inputs = conf['sensors']
        print self.inputs
        self.publish_bcast = []
        self.outputs = conf['actuators']
        self.motors = conf['motors']
        print self.outputs
        self.init_inputs(self.inputs)
        self.init_outputs(self.outputs)
        self.init_serve(ID)
        ##############################################

        # Enumerated lists for each #########
        self.services = services
        self.languages = conf['languages']
        self.protocols = conf['protocols']
        self.abilities = conf['abilities']
        self.resources = conf['resources']
        ####################################

        # Variables manipulated by multiple threads ###
        self.adaptive_state = []
        ##############################################

        ## Contains info specific to the internal state of the agent such as: state, health attributes etc.
        self.mycore = core_aboutme.Core(willingness, ID, conf['battery'], sensors, actuators, motors)
        self.log.write_log_file(self.log.stdout_log, 'init gitagent ' + str(self.mycore.sensmot) + '\n')
        ## Contains mixed info ############################################################################
        self.myknowledge = knowledge.Knowledge0()

        # use simulation functions
        self.simulation = simulation

        print self.inputs, self.outputs, self.motors, self.languages, self.protocols, conf['battery']

        #########this is a publisher which publishes to pseudo-planner --- must be integrated like the others --- TEMPORARY code
        self.pub_plan_status = rospy.Publisher('/environment/plan', Protocol_Msg, queue_size=10)

    ###############################################################################
    # time.sleep(200)

    def fsm(self):
        while not rospy.is_shutdown():
            # Agent stopping function
            self.change_selfstate_v2()
            # normally you might want to estimate a value that corresponds to the cost of each cycle
            # self.mycore.battery_change(-1)
            self.mycore.sensory_motor_state_mockup()
            self.mycore.check_health()
            # funksioni meposhte mund te ekzekutohet ne paralel --> per tu zhvilluar me tej ne nje moment te dyte
            self.publish2sensormotor(self.services)
            self.log.write_log_file(self.log.stdout_log, '[fsm ' + str(self.simulation.fsm) + '] current state: ' + str(
                self.mycore.state) + '\n')

            ##MOVE ###############################################################################
            self.myknowledge.position2D = self.simulation.move(self.myknowledge.position2D)
            self.log.write_log_file(self.log.stdout_log,
                                    '[fsm ' + str(self.simulation.fsm) + '] self.myknowledge.position2D: ' + str(
                                        self.myknowledge.position2D) + '\n')
            self.publish_bcast[1].publish(self.mycore.create_message(self.myknowledge.position2D, 'position'))
            ######################################################################################

            self.fsm_step()
        return

    def agent_quit_running(self):
        if (timeit.default_timer() - self.start_time) > self.end_time:
            self.log.write_log_file(self.log.stdout_log, '[fsm ' + str(self.simulation.fsm) + '] current state: quitting - '
                                                                                              'timer reached')
            return


    def fsm_step(self):
        self.simulation.fsm = self.simulation.inc_iterationstamps(self.simulation.fsm)

        if self.mycore.state == 0:
            self.idle()
        elif self.mycore.state == 1:
            self.interact()
        elif self.mycore.state == 2:
            self.execute_v2()
        elif self.mycore.state == 3:
            self.regenerate()
        elif self.mycore.state == 4:
            self.dead()

    def change_selfstate_v2(self):
        if not self.myknowledge.plan_pending_eval.empty():
            self.log.write_log_file(self.log.stdout_log,
                                    '[fsm ' + str(self.simulation.fsm) + '] adaptive state: True\n')

            self.myknowledge.lock.acquire()
            self.myknowledge.old_state = self.mycore.state
            self.mycore.state = 1
            self.log.write_log_file(self.log.stdout_log,
                                    '[fsm ' + str(self.simulation.fsm) + '] ' + str(self.myknowledge.old_state) + str(
                                        self.mycore.state) + '\n')
            self.myknowledge.lock.release()
        else:
            self.log.write_log_file(self.log.stdout_log,
                                    '[fsm ' + str(self.simulation.fsm) + '] adaptive state: False\n')

    def eval_temp_2(self):

        self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(self.simulation.interact) + ']\n')

        rate = -1000
        rate_depend = -1000

        if self.myknowledge.attempted_jobs == 0:
            rate = 0.0
        else:
            rate = 1.0 * self.myknowledge.completed_jobs / self.myknowledge.attempted_jobs

        if self.myknowledge.attempted_jobs_depend == 0:
            rate_depend = 0.0
        else:
            rate_depend = 1.0 * self.myknowledge.completed_jobs_depend / self.myknowledge.attempted_jobs_depend

        ## Here put the new fuzzy evaluation function
        accept = True

        self.log.write_log_file(self.log.stdout_log,
                                '[adapt ' + str(self.simulation.interact) + '] accept ' + str(accept) + '\n')

        if accept:
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(self.simulation.interact) + '] adapted\n')
            ## Take plan-request out of queue, and put the tasks into the queue for tasks the agent has committed to
            plan = self.myknowledge.plan_pending_eval.get()
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] ' + str(plan) + '\n\n')

            for x in plan:
                self.log.write_log_file(self.log.stdout_log,
                                        '[adapt ' + str(self.simulation.interact) + '] ' + str(x) + '\n')
                self.myknowledge.task_queue.put(x)
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] put tasks in queue\n')

            self.myknowledge.count_posReq = self.myknowledge.count_posReq + 1

            self.myknowledge.attempted_jobs = self.myknowledge.attempted_jobs + 1

            self.mycore.state = 2
            # self.myknowledge.service = self.services[self.myknowledge.task_idx]

            self.myknowledge.helping = True
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] helping: ' + str(
                                        self.myknowledge.helping) + '\n')

        else:
            print 'keep at what you\'re doing'
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(self.simulation.interact) + '] do not adapt\n')
            self.mycore.state = self.myknowledge.old_state

    def idle(self):
        print 'im in idle'
        self.simulation.idle = self.simulation.inc_iterationstamps(self.simulation.idle)
        self.log.write_log_file(self.log.stdout_log, '[fsm ' + str(self.simulation.idle) + ']\n')
        self.generate_goal()
        self.commit2goal()

    def interact(self):
        print 'im in interact'
        self.simulation.interact = self.simulation.inc_iterationstamps(self.simulation.interact)

        self.eval_temp_2()

        self.evaluate_my_state()
        self.evaluate_agent()
        self.evaluate_request()
        self.commit2agent()

    def send_status(self, plan_id):
        if not self.myknowledge.current_plan_id == plan_id and self.myknowledge.current_plan_id > 0:
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(
                self.simulation.interact) + '] planID: %d has finished, send \'1\'\n' % self.myknowledge.current_plan_id)
            message = Protocol_Msg()
            message.performative = 'plan_status'
            message.sender = str(self.mycore.ID)
            message.rank = 10
            message.receiver = 'all'
            message.language = 'shqip'
            message.ontology = 'shenanigans'
            message.urgency = 'INFO'
            message.content = str(self.myknowledge.current_plan_id) + '|1'
            message.timestamp = time.strftime('%X', time.gmtime())
            if not rospy.is_shutdown():
                self.pub_plan_status.publish(message)
                self.log.write_log_file(self.log.stdout_log,
                                        '[adapt ' + str(self.simulation.interact) + '] message ' + str(
                                            message) + ' published \n')

        self.myknowledge.current_plan_id = plan_id
        self.log.write_log_file(self.log.stdout_log, '[current plan] planID: %d\n' % plan_id)

    def execute_v2(self):
        self.simulation.execute = self.simulation.inc_iterationstamps(self.simulation.execute)

        self.log.write_log_file(self.log.stdout_log,
                                '[execute ' + str(self.simulation.execute) + ']' + str(self.myknowledge.service) + '\n')
        self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
            self.myknowledge.service_id) + '\n')
        self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
            self.myknowledge.iteration) + '\n')

        if self.myknowledge.service_id == -1 and self.myknowledge.iteration == -1:
            if not self.myknowledge.task_queue.empty():
                self.myknowledge.service = self.myknowledge.task_queue.get()
                self.myknowledge.service_id = int(self.myknowledge.service['id'])
                self.myknowledge.iteration = 1

                # self.send_status(int(self.myknowledge.service['planID']))

                ## Detect task difficulty - from nr of required abilities
                self.myknowledge.difficulty = self.simulation.detect_difficulty(self.myknowledge.service)

                self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
                    self.myknowledge.service) + '\n')
                self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
                    self.myknowledge.service_id) + '\n')
                self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
                    self.myknowledge.iteration) + '\n')
                self.log.write_log_file(self.log.stdout_log,
                                        '[execute ' + str(self.simulation.execute) + '] ->Difficulty: ' + str(
                                            self.myknowledge.difficulty) + '\n')
                self.execute_step_v3()
            else:
                self.mycore.state = 0
                self.log.write_log_file(self.log.stdout_log, '[execute ' + str(self.simulation.execute) + ']' + str(
                    self.mycore.state) + '\n')
        else:
            self.log.write_log_file(self.log.stdout_log,
                                    '[execute ' + str(self.simulation.execute) + '] continue working\n')
            self.execute_step_v3()

    def execute_step_v2(self):
        dependencies = self.simulation.sim_dependencies(self.myknowledge.service)

        self.log.write_log_file(self.log.stdout_log,
                                '[run_step ' + str(self.simulation.execute) + '] dependencies: %f \n' % dependencies)

        self.log.write_log_file(self.log.stdout_log,
                                '[run_step ' + str(self.simulation.execute) + '] fuzzy inputs: %f, health: %f\n' % int(
                                    dependencies, sum([self.mycore.sensmot, self.mycore.battery])))

        start_time = timeit.default_timer()
        depend_fuzzy = self.mycore.willing2ask(
            [sum([self.mycore.sensmot, self.mycore.battery]), 0.7, dependencies, 0.5])
        self.simulation.fuzzy_time.append(timeit.default_timer() - start_time)

        self.log.write_log_file(self.log.stdout_log,
                                '[run_step ' + str(self.simulation.execute) + '] depend_fuzzy: %f \n' % int(
                                    depend_fuzzy))

        if self.myknowledge.iteration < int(self.myknowledge.service['iterations']):
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] Running task: %d, iteration: %d\n' % (
                                    self.myknowledge.service_id, self.myknowledge.iteration))
            self.myknowledge.iteration = self.myknowledge.iteration + 1
        else:
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] Task: %d done\n' % self.myknowledge.service_id)
            self.myknowledge.service_id = -1
            self.myknowledge.iteration = -1

    ##Instead of iteration, pause for some prespecified time
    def execute_step_v3(self):
        dependencies_abil, dependencies_res, req_missing = self.simulation.sim_dependencies(self.myknowledge.service)

        self.log.write_log_file(self.log.stdout_log,
                                '[run_step ' + str(self.simulation.execute) + '] fuzzy inputs: %f, %f, health: %f\n' % (
                                dependencies_abil, dependencies_res, sum([self.mycore.sensmot, self.mycore.battery])))

        start_time = timeit.default_timer()
        depend = self.mycore.ask_4help(sum([self.mycore.sensmot, self.mycore.battery]), dependencies_abil,
                                             dependencies_res,  0.5, 0.5, 0.5,
                                             0.5, 0.5)
        # depend_fuzzy = self.mycore.willing2ask_fuzzy(
        #     [sum([self.mycore.sensmot, self.mycore.battery]), 0.7, dependencies, 0.5])
        self.simulation.fuzzy_time.append(timeit.default_timer() - start_time)

        self.log.write_log_file(self.log.stdout_log,
                                '[run_step ' + str(self.simulation.execute) + '] depend_fuzzy: ' + str(
                                    depend) + '\n')

        if req_missing and not depend:
            self.simulation.required_missing_noreq = self.simulation.required_missing_noreq + 1
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] There should have been a request: ' + str(
                self.simulation.required_missing_noreq / float(self.simulation.required_missing)) + '\n')

        if depend:
            self.simulation.requests[self.myknowledge.difficulty] = self.simulation.requests[
                                                                        self.myknowledge.difficulty] + 1
            exec_time = self.simulation.additional_delay[self.myknowledge.difficulty] + self.simulation.delay[
                self.myknowledge.difficulty]
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] difficulty: %f, delay: %f, addi: %f\n' % (
                                    self.myknowledge.difficulty, self.simulation.delay[self.myknowledge.difficulty],
                                    self.simulation.additional_delay[self.myknowledge.difficulty]))
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] Ask for help\n ...Wait for %f' % exec_time)
            self.simulation.exec_times[self.myknowledge.difficulty] = self.simulation.exec_times[
                                                                          self.myknowledge.difficulty] + exec_time
            time.sleep(exec_time)
            self.myknowledge.service_id = -1
            self.myknowledge.iteration = -1
            # Assume that less energy is consumed when asking for help -- someone else is doing the deed
            self.mycore.battery_change(0.2 * int(self.myknowledge.service['energy']))
        else:
            exec_time = self.simulation.delay[self.myknowledge.difficulty]
            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] Do it yourself\n ...Wait for %f' % exec_time)
            self.simulation.exec_times[self.myknowledge.difficulty] = self.simulation.exec_times[
                                                                          self.myknowledge.difficulty] + exec_time

            self.log.write_log_file(self.log.stdout_log, '[run_step ' + str(
                self.simulation.execute) + '] difficulty: %f, delay: %f, addi: %f\n' % (
                                    self.myknowledge.difficulty, self.simulation.delay[self.myknowledge.difficulty],
                                    self.simulation.additional_delay[self.myknowledge.difficulty]))
            time.sleep(exec_time)
            self.myknowledge.service_id = -1
            self.myknowledge.iteration = -1
            # diminish by the energy required by the task
            self.mycore.battery_change(int(self.myknowledge.service['energy']))

    def regenerate(self):
        print 'im in regenerate'
        self.simulation.regenerate = self.simulation.inc_iterationstamps(self.simulation.regenerate)

        self.debug_self()
        self.fix_bugs()

    def dead(self):
        print 'im in dead'
        self.simulation.dead = self.simulation.inc_iterationstamps(self.simulation.dead)

        self.evaluate_self()
        self.evaluate_environment()
        self.evaluate_selfmending()

        # Dirty trick to end the simulation
        return

    # MUST be overriden in the child class, depending on the different types of inputs!
    def init_inputs(self, inputs):
        pass

    def init_outputs(self, outputs):
        for x in outputs:
            self.publish_bcast.append(rospy.Publisher(x, Protocol_Msg, queue_size=200))
        print self.publish_bcast

    def generate_goal(self):
        if random.random() > 0.7:
            senderId = -1
            planId = -random.randint(1, 100)
            tID = random.randint(1, 100)
            iterations = random.randint(1, 100)
            energy = random.randint(1, 100)
            reward = random.randint(1, 100)
            tName = 'some task'
            startLoc = [2, 3]
            endLoc = [5, 6]
            noAgents = random.randint(1, 100)
            equipment = [['pip'], ['pop'], ['pup']]
            abilities = ['halloumi']
            res = ['mozarella']
            estim_time = random.random() * random.randint(1, 100)

            tasks = [{'senderID': senderId, 'planID': planId, 'id': tID, 'iterations': iterations, 'energy': energy,
                      'reward': reward, 'name': tName, 'startLoc': startLoc, 'endLoc': endLoc, 'noAgents': noAgents,
                      'equipment': equipment, 'abilities': abilities, 'resources': res, 'estim_time': estim_time}]

            self.log.write_log_file(self.log.stdout_log,
                                    '[wander ' + str(self.simulation.idle) + '] Chosen service: ' + str(tasks) + '\n')

            for x in tasks:
                self.log.write_log_file(self.log.stdout_log,
                                        '[adapt ' + str(self.simulation.interact) + '] ' + str(x) + '\n')
                self.myknowledge.task_queue.put(x)

            self.mycore.state = 2
        else:
            self.log.write_log_file(self.log.stdout_log, '[wander ' + str(
                self.simulation.idle) + '] do nothing - zot jepi atij qe rri kot :DD\n')

    def plan2goal(self):
        pass

    def commit2goal(self):
        pass

    def evaluate_my_state(self):
        pass

    def evaluate_agent(self):
        pass

    def evaluate_request(self):
        pass

    def commit2agent(self):
        pass

    def evaluate_self(self):
        pass

    def evaluate_environment(self):
        pass

    def evaluate_selfmending(self):
        pass

    def update_culture(self, help, expertise, load):
        pass

    def debug_self(self):
        pass

    def fix_bugs(self):
        pass

    def make_request(self):
        pass

    def resolve_dependencies(self, service):
        if len(service) > 4:
            return True
        else:
            return False

    def eval_plan(self):
        pass

    def eval_temp(self):
        for x in self.services:
            if x[0] == self.myknowledge.service_req[self.myknowledge.client_index]:
                self.myknowledge.task_idx = self.services.index(x)

        # Decide if it is good to accept request

        self.log.write_log_file(self.log.stdout_log,
                                '[adapt ' + str(self.simulation.interact) + '] client: %d, service_resp: %s\n' % (
                                self.myknowledge.current_client[self.myknowledge.client_index],
                                str(self.myknowledge.service_resp[self.myknowledge.client_index])) + '[adapt ' + str(
                                    self.simulation.interact) + '] old serve: %s\n' % (str(self.myknowledge.service)))

        rate = -1000
        rate_depend = -1000

        if self.myknowledge.attempted_jobs == 0:
            rate = 0.0
        else:
            rate = 1.0 * self.myknowledge.completed_jobs / self.myknowledge.attempted_jobs

        if self.myknowledge.attempted_jobs_depend == 0:
            rate_depend = 0.0
        else:
            rate_depend = 1.0 * self.myknowledge.completed_jobs_depend / self.myknowledge.attempted_jobs_depend

        accept = self.keep_request(self.myknowledge.current_client[self.myknowledge.client_index],
                                   self.services[self.myknowledge.task_idx], self.myknowledge.old_state,
                                   self.myknowledge.service, rate, rate_depend)
        if self.simulation.handle > 0:
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] handled = %d\n' % (
                                    self.simulation.handle))
            self.myknowledge.timeouts_xinteract.append(1.0 * self.myknowledge.timeouts / self.simulation.handle)
        else:
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] nope, nope, nope\n')
            print 'nope'

        self.log.write_log_file(self.log.stdout_log,
                                '[adapt ' + str(self.simulation.interact) + '] accept ' + str(accept) + '\n')

        if accept:
            ############################ playing with 'queues' - THIS PART IS NOT THREAD-SAFE, NOR FINAL, nor does it remove anything from the .._eval list ###########################
            self.myknowledge.task_queue = self.myknowledge.task_pending_eval
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(self.simulation.interact) + '] ' + str(
                self.myknowledge.task_queue) + '\n')
            ########################################################################################################################
            self.myknowledge.count_posReq = self.myknowledge.count_posReq + 1
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(self.simulation.interact) + '] adapted\n')

            self.myknowledge.attempted_jobs = self.myknowledge.attempted_jobs + 1

            self.myknowledge.iteration = 1
            self.mycore.state = 2
            self.myknowledge.service = self.services[self.myknowledge.task_idx]

            if len(self.myknowledge.service) > 4:
                self.myknowledge.attempted_jobs_depend = self.myknowledge.attempted_jobs_depend + 1

            self.myknowledge.helping = True
            self.log.write_log_file(self.log.stdout_log,
                                    '[adapt ' + str(self.simulation.interact) + '] service: ' + str(
                                        self.myknowledge.service) + '\n' + '[adapt ' + str(
                                        self.simulation.interact) + '] helping: ' + str(
                                        self.myknowledge.helping) + '\n')

        else:
            print 'keep at what you\'re doing'
            # praktikisht e le pergjysem kerkesen
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(
                self.simulation.interact) + '] keep at what you\'re doing\n' + '[adapt ' + str(
                self.simulation.interact) + '] before if: current client_index: ' + str(
                self.myknowledge.client_index) + '\n')
            if not self.myknowledge.client_index == -1:
                self.myknowledge.lock.acquire()
                self.myknowledge.service_req[self.myknowledge.client_index] = -1
                self.myknowledge.service_resp_content[self.myknowledge.client_index] = -1
                self.myknowledge.service_resp[self.myknowledge.client_index] = True
                self.myknowledge.lock.release()

            self.myknowledge.client_index = self.myknowledge.old_client_index
            self.log.write_log_file(self.log.stdout_log, '[adapt ' + str(
                self.simulation.interact) + '] after old state: current client_index: ' + str(
                self.myknowledge.client_index) + '\n')

            self.mycore.state = self.myknowledge.old_state

    def keep_request(self, client, new_service, state, old_service, jobs_dropped, depend_done):
        accept = False
        ## what you need to make only one agent dynamic ############################################################################################################
        if self.mycore.ID == 7:
            drop_rate = jobs_dropped - self.myknowledge.past_jobs_dropped
            self.log.write_log_file(self.log.stdout_log,
                                    '[dep_delta] dropped: %f, past_dropped: %f, past delta: %f\n' % (
                                    jobs_dropped, self.myknowledge.past_jobs_dropped, self.mycore.willingness[1]))

            # self.delta = self.delta - (jobs_dropped - self.past_jobs_dropped) * jobs_dropped
            if jobs_dropped > self.myknowledge.HIGH:
                self.mycore.willingness[1] = self.mycore.willingness[1] - self.myknowledge.step
                self.log.write_log_file(self.log.stdout_log, '[dep_delta] delta decreased %f by step %f\n' % (
                self.mycore.willingness[1], self.myknowledge.step))
            elif jobs_dropped < self.myknowledge.LOW:
                self.mycore.willingness[1] = self.mycore.willingness[1] + self.myknowledge.step
                self.log.write_log_file(self.log.stdout_log, '[dep_delta] delta increased %f by step %f\n' % (
                self.mycore.willingness[1], self.myknowledge.step))
            elif abs(drop_rate) >= 0.01:
                self.log.write_log_file(self.log.stdout_log, '[dep_delta] entered else, L < jb_d < H\n')
                inc_dec = 1 if drop_rate >= 0 else -1
                self.mycore.willingness[1] = self.mycore.willingness[1] - inc_dec * self.myknowledge.step
                self.log.write_log_file(self.log.stdout_log,
                                        '[dep_delta] delta change %f by step %f, inc_dec = %d\n' % (
                                        self.mycore.willingness[1], self.myknowledge.step, inc_dec))
            else:
                self.log.write_log_file(self.log.stdout_log,
                                        '[dep_delta] delta doesn\'t change, else condition, %f by step %f\n' % (
                                        self.mycore.willingness[1], self.myknowledge.step))
                print 'no change'

            # fit to [0,1]
            if self.mycore.willingness[1] > 1.0:
                self.mycore.willingness[1] = 1.0
            elif self.mycore.willingness[1] < 0.0:
                self.mycore.willingness[1] = 0.0

            self.log.write_log_file(self.log.stdout_log, '[dep_delta] delta = %f\n' % self.mycore.willingness[1])
            self.myknowledge.past_jobs_dropped = jobs_dropped
        ###########################################################################################################################################################

        self.myknowledge.moving_delta_sorted.append(self.mycore.willingness[1])
        self.myknowledge.moving_drop_jobs.append(jobs_dropped)
        self.myknowledge.moving_depend_done.append(depend_done)

        self.log.write_log_file(self.log.stdout_log,
                                '[dep_delta] moving_delta_sorted = %s\n' % str(self.myknowledge.moving_delta_sorted))
        self.log.write_log_file(self.log.stdout_log,
                                '[dep_delta] moving_drop_jobs = %s\n' % str(self.myknowledge.moving_drop_jobs))

        match = False
        if self.myknowledge.moving_delta:
            for x in self.myknowledge.moving_delta:
                if client in x:
                    self.myknowledge.moving_delta[self.myknowledge.moving_delta.index(x)].append(
                        self.mycore.willingness[1])
                    match = True
                    break
            if not match:
                self.myknowledge.moving_delta.append([client, self.mycore.willingness[1]])
        else:
            self.myknowledge.moving_delta.append([client, self.mycore.willingness[1]])

        check_rand = random.random()

        if check_rand < self.mycore.willingness[1]:
            accept = True

        print 'ACCEPT: ', accept

        return accept

    def publish2sensormotor(self, raw_content):
        if not rospy.is_shutdown():
            print rospy.get_name()
            self.publish_bcast[0].publish(self.mycore.create_message(raw_content, ''))
        else:
            print 'rospy is shutdown'

    def init_serve(self, agentid):
        myservice = '/robot' + str(agentid) + '/serve'
        print 'DECLARING my service'
        srv = rospy.Service(myservice, Protocol_Srv, self.handle_serve)

    def handle_serve(self, request):
        pass

    def call_serve(self, server, myid, request, anyone_index):
        pass
