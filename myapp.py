import os
import json
import io
import time
import untangle
import networkx as nx

controllerIp = '128.163.232.72:8080'

#build topology
Network = nx.Graph()

#parse rspec           
'''
obj = untangle.parse("topology.xml")
for node in obj.rspec.node:
	print(node["client_id"])
        if node["client_id"]<>'GDGN0' and node["client_id"]<>'AAGCTRL0':
        	for interface in node.interface:
                	print(interface["client_id"])
                        print(interface.ip["address"])
'''
# Get switch and link information from the controller
command = "curl -s http://%s/wm/core/controller/switches/json" % controllerIp
result = os.popen(command).read()
parsedResult = json.loads(result)
#print parsedResult
for result in parsedResult:
#	print result['switchDPID']
	Network.add_node(result['switchDPID'], address=result['inetAddress'])
	
print Network.nodes(data=True)
#get statistics
'''
enable statistics in the switches

command = "curl -X POST -d '' http://%s/wm/statistics/config/enable/json" % controllerIp
os.popen(command).read()
command
'''
#add route


#delete route
