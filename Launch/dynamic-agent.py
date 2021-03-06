#!/usr/bin/env python
#Creates launch file for one single agent
import sys

def write_launch_file(theta, delta, depends, provaNr):

	try: 
		launch = open('agent_'+str(theta)+'_'+str(delta)+'_'+str(depends)+'.launch', 'w')
		launch.write('<launch>\n')

		launch.write('	<arg name="id"/>\n')
		launch.write('	<node pkg="gitagent" type="agent_run.py" name="brain_node" output="log" launch-prefix="xterm -e">\n')
		launch.write('		<param name="myID" value="$(arg id)" />\n')
		launch.write('		<param name="myTheta" value="'+str(theta)+'" />\n')
		launch.write('		<param name="myDelta" value="'+str(delta)+'" />\n')
		launch.write('		<param name="myDepend" value="'+str(depends)+'" />\n')
		launch.write('		<param name="provaNr" value="'+str(provaNr)+'" />\n')
		launch.write('	</node>')

		launch.write('	<node pkg="gitagent" type="msg_PUnit.py" name="msg_punit" output="log" launch-prefix="xterm -e">\n')
		launch.write('		<param name="myID" value="$(arg id)" />\n')
		launch.write('	</node>\n')

		
		launch.write('</launch>\n')
		launch.close()
	except IOError:
		print "Error: can\'t find file or read data"
	

if __name__ == '__main__':
	if not len(sys.argv) == 5:
		print 'Usage: ./dynamic-agent.py theta delta depends trial_number'
		print 'write trial_number as a string as follows popsize_trialnumber'
	else:
		write_launch_file(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
