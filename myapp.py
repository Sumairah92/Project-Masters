import os
import json
import io
import time
import untangle
import time
import re
import networkx as nx

#Declare variables

controllerIp = '128.163.232.72:8080'
dpids = list()
edges = list()
interfaces = list()
links = list()
Network = nx.Graph()
Bandwidth_t1 = dict()
Bandwidth_t2 = dict()
BandwidthUsage = dict()

# Get switch and link information from the controller

#-----Get all DPIDs-------#

command = "curl -s http://%s/wm/core/controller/switches/json" % controllerIp
result = os.popen(command).read()
parsedResult = json.loads(result)
for result in parsedResult:
        d = result['switchDPID']
        dpids.append(d)

#------- Get node names to link with DPIDs------#

command = "curl -s http://%s/wm/core/switch/all/desc/json" % controllerIp
result = os.popen(command).read()
parsedResultName = json.loads(result)

#-------Get Port information for switch interfaces------#

command = "curl -s http://%s/wm/core/switch/all/features/json" % controllerIp
result = os.popen(command).read()
parsedResultPorts = json.loads(result)

#parse rspec and get topology information from controller

obj = untangle.parse("topology.xml")
for link in obj.rspec.link:
	for interface in link.interface_ref:
		I = {'interface': interface["client_id"],'name':link["client_id"]}
		links.append(I)

for node in obj.rspec.node:
	if node["client_id"]<>'GDGN0' and node["client_id"]<>'AAGCTRL0':
        	Network.add_node(node["client_id"])
		count = 0
        	for interface in node.interface:
			count += 1
			for i,x in enumerate(links):
        			if x["interface"] == interface["client_id"]:
                			thisLink = x["name"]
			mac= re.sub(r'(.{2})(?!$)', r'\1:',interface["mac_address"])
			for d in dpids:
        			for i,p in enumerate(parsedResultPorts[d]["portDesc"]):
                			if (parsedResultPorts[d]["portDesc"][i]['hardwareAddress']) == mac:
						port=parsedResultPorts[d]["portDesc"][i]['portNumber']
            		I = { 'name' : interface["client_id"],
                  		'IP' : interface.ip["address"],
			       'MAC' : mac,
			       'link' : thisLink,
			       'Port' : port}
            		interfaces.append(I)
		for d in dpids:
        		if parsedResultName[d]['desc']['datapathDescription'] == node["client_id"]:
				dp = d
    	host = { 'name' : node["client_id"],
        	 'interfaces' : interfaces,
		 'DPID' : dp,
		 'linkNum' : count}

    	Network.add_node(host['name'], linkNum=host['linkNum'], interfaces=host['interfaces'], DPID = host['DPID'])
    	interfaces= []
	dp = None

for nodes in Network.nodes():
	for i,interface in enumerate(Network.node[nodes]['interfaces']):
		L1 =  Network.node[nodes]['interfaces'][i]['link']
		e1 = nodes
		for nodes2 in Network.nodes():
			for i2,interface2 in enumerate(Network.node[nodes2]['interfaces']):
				if (Network.node[nodes2]['interfaces'][i2]['link']== L1) and (nodes2 <> e1):
					e2 = nodes2
		Network.add_edge(e1,e2)

#print Network.nodes(data=True)

#for path in nx.all_simple_paths(Network, source='h2', target='h3'):
#    print path
print "Topology created"

#get statistics

print "Preparing for querying statistics"
time.sleep(5)

#------enable statistics in the switches---#

command = "curl -X POST -d '' http://%s/wm/statistics/config/enable/json" % controllerIp
os.popen(command).read()

while True:

#----------Query for stats at t1----------#

        for nodes in Network.nodes():
		if Network.node[nodes]['DPID'] is not None:
        		for i,interface in enumerate(Network.node[nodes]['interfaces']):
                		P =  Network.node[nodes]['interfaces'][i]['Port']
				if P <> 'local':
                			command = "curl http://%s/wm/statistics/bandwidth/'%s'/'%s'/json" % (controllerIp, Network.node[nodes]['DPID'],P)
                			result=os.popen(command).read()
                			parsedResult = json.loads(result)
                			for result in parsedResult:
						Bandwidth_t1[result['dpid']+result['port']] = int(result['bits-per-second-tx'])+int(result['bits-per-second-rx'])
	
	time.sleep(10)
#----------Query for stats at t2----------#

	for nodes in Network.nodes():
        	if Network.node[nodes]['DPID'] is not None:
                	for i,interface in enumerate(Network.node[nodes]['interfaces']):
                        	P =  Network.node[nodes]['interfaces'][i]['Port']
                        	if P <> 'local':
                                        command = "curl http://%s/wm/statistics/bandwidth/'%s'/'%s'/json" % (controllerIp, Network.node[nodes]['DPID'],P)
                                        result=os.popen(command).read()
                                        parsedResult = json.loads(result)
                                        for result in parsedResult:
						Bandwidth_t2[result['dpid']+result['port']] = int(result['bits-per-second-tx'])+int(result['bits-per-second-rx'])

#----------Calculate Bandwidth Difference----------#

	for nodes in Network.nodes():
                if Network.node[nodes]['DPID'] is not None:
                        for i,interface in enumerate(Network.node[nodes]['interfaces']):
                                P =  Network.node[nodes]['interfaces'][i]['Port']
                                if P <> 'local':
                                	BandwidthUsage[Network.node[nodes]['DPID']+P] = Bandwidth_t2[Network.node[nodes]['DPID']+P] - Bandwidth_t1[Network.node[nodes]['DPID']+P]

	print BandwidthUsage	
#add route


