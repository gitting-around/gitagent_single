#!/usr/bin/env python
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
import math
import traceback
import pdb


# Plan format
# 

# Task format
# Keep mine for now, but it will need to change

class PseudoPlanner:
    def __init__(self, plan):

        self.plan4agents = plan

        self.completed_plans = 0
        self.sent_plans = [0, 0, 0]
        self.plans_so_far = []
        self.plan_complexity = 0

        rospy.init_node('pseudo_planner', anonymous=True)
        self.publish_plan = rospy.Publisher('/environment/plan', Protocol_Msg, queue_size=200)
        # rospy.Subscriber('/environment/plan', Protocol_Msg, self.status)

        self.used_planID = []

        sim = simulation.Simulation0()
        self.tasks, self.unformattedTasks = sim.get_tasks('specs')

    def status(self, data):
        if not int(data.sender) == 0:
            if data.performative == 'plan_status':
                print 'received plan status message'
                print self.plan4agents
                print 'Agent\'s response: ' + str(data.content) + '\n'

                if int(data.content) == 1:
                    self.completed_plans = self.completed_plans + 1
                    self.generate_plan([1], 10)
                else:
                    print 'plan not completed'

            else:
                print 'some other type of status report -- shouldn\'t happen yet'
        else:
            print 'Ignore messages from self'

    def create_message(self, plan):
        message = Protocol_Msg()
        message.performative = 'highlevelplan'
        message.sender = '0'
        message.rank = 10
        message.receiver = 'all'
        message.language = 'shqip'
        message.ontology = 'shenanigans'
        message.urgency = 'INFO'
        message.content = self.create_msg_content(plan)
        message.timestamp = time.strftime('%X', time.gmtime())
        return message

    def create_msg_content(self, plan):

        # content = str(plan[0]) + '\n'
        # plan.pop(0)
        # for x in plan:
        # content = content + str(x[0]) + '|'
        # for y in x[1]:
        # content = content + str(y)
        # if x[1].index(y) < len(x[1])-1:
        # content = content  + ' '
        # if plan.index(x) < len(plan)-1:
        # content = content + '\n'

        # pdb.set_trace()
        print plan
        content = str(plan[0]) + '\n'
        plan.pop(0)
        for x in plan:
            content = content + str(x[0]) + '$'
            for y in x[1]:
                content = content + str(y) + '#'

        print content
        return content

    def publish_new_plan(self):

        rate = rospy.Rate(10)  # 10Hz
        repeat_loop = 4

        while not rospy.is_shutdown():
            if self.plan_complexity > 2:
                return

            plan = self.create_message(self.plan4agents)
            for i in range(0, repeat_loop):
                # pdb.set_trace()
                self.publish_plan.publish(plan)
                print plan
                print '\n\n'
                rate.sleep()
            # pdb.set_trace()
            self.generate_plan([1], 10)

    def generate_plan(self, agents, plan_length):
        # agents - list of ids
        # tasks - list of dictionaries, each dictionary represents a task
        # plan_length - int determining the number of tasks - to be kept fixed
        # plan_complexity - 0, 1, 2 - low, medium, high

        # pdb.set_trace()

        self.sent_plans[self.plan_complexity] = self.sent_plans[self.plan_complexity] + 1
        if self.sent_plans[self.plan_complexity] > 50:
            self.plan_complexity = self.plan_complexity + 1
            if self.plan_complexity > 2:
                return

        plan = []
        plan_id = random.randint(1, 1000)
        while plan_id in self.plans_so_far:
            print self.plans_so_far
            print plan_id
            plan_id = random.randint(1, 1000)

        self.plans_so_far.append(plan_id)
        print self.plans_so_far
        print plan_id
        plan.append(plan_id)

        for x in agents:
            temp = []
            if self.plan_complexity == 0:
                for i in range(0, int(math.floor(0.75 * plan_length))):
                    temp.append(self.unformattedTasks[0])
                for i in range(0, int(math.floor(0.25 * plan_length))):
                    temp.append(self.unformattedTasks[1])
            elif self.plan_complexity == 1:
                for i in range(0, int(math.floor(0.50 * plan_length))):
                    temp.append(self.unformattedTasks[0])
                for i in range(0, int(math.floor(0.25 * plan_length))):
                    temp.append(self.unformattedTasks[1])
                for i in range(0, int(math.floor(0.25 * plan_length))):
                    temp.append(self.unformattedTasks[2])
            elif self.plan_complexity == 2:
                for i in range(0, int(math.floor(0.20 * plan_length))):
                    temp.append(self.unformattedTasks[0])
                for i in range(0, int(math.floor(0.25 * plan_length))):
                    temp.append(self.unformattedTasks[1])
                for i in range(0, int(math.floor(0.50 * plan_length))):
                    temp.append(self.unformattedTasks[2])
            plan.append([x, temp])

        print plan

        self.plan4agents = plan


if __name__ == '__main__':
    # pdb.set_trace()
    stderr_file = '/home/mfi01/catkin_ws/results/error_plan'
    f = open(stderr_file, 'w+')
    orig_stderr = sys.stderr
    sys.stderr = f

    stdout_file = '/home/mfi01/catkin_ws/results/stdout_plan'
    s = open(stdout_file, 'w+')
    orig_stdout = sys.stdout
    try:
        plan = [1, [1, [2]], [2, [4]], [3, [7]]]
        # pdb.set_trace()
        pplanner = PseudoPlanner(plan)
        pplanner.generate_plan([1], 10)
        pplanner.publish_new_plan()
    # rospy.spin()
    except rospy.ROSInterruptException:
        traceback.print_exc()
        raise
    except (AttributeError, TypeError, ValueError, NameError):
        traceback.print_exc()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc()
        raise
    finally:
        sys.stderr = orig_stderr
        f.close()
        sys.stdout = orig_stdout
        s.close()
