import os
import json
import io
import time
import untangle
import time
import re
import httplib
import networkx as nx

#Declare variables

controllerIp = '128.163.232.72:8080'
dpids = list()
edges = list()
interfaces = list()
links = list()
interswitchLinks = list()
Network = nx.Graph()
Bandwidth_t1 = dict()
Bandwidth_t2 = dict()
BandwidthUsage = dict()

#Declare static flowpusher class

class StaticFlowPusher(object):
 
    def __init__(self, server):
        self.server = server
 
    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])
 
    def set(self, data):
        ret = self.rest_call(data, 'POST')
        return ret[0] == 200
 
    def remove(self, objtype, data):
        ret = self.rest_call(data, 'DELETE')
        return ret[0] == 200
 
    def rest_call(self, data, action):
        path = '/wm/staticflowpusher/json'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()
        return ret

pusher = StaticFlowPusher('128.163.232.72')

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

#------Add edges and identify interswitch Links-----#
for nodes in Network.nodes():
	for i,interface in enumerate(Network.node[nodes]['interfaces']):
		L1 =  Network.node[nodes]['interfaces'][i]['link']
		e1 = nodes
		for nodes2 in Network.nodes():
			for i2,interface2 in enumerate(Network.node[nodes2]['interfaces']):
				if (Network.node[nodes2]['interfaces'][i2]['link']== L1) and (nodes2 <> e1):
					e2 = nodes2
					if "s" in nodes2 and "s" in nodes:
						interswitchLinks.append(L1)
		Network.add_edge(e1,e2)
interswitchLinks = list(set(interswitchLinks))

#print Network.nodes(data=True)
								

print "Topology created"
count = 0

def generate_rule_for_path(path,sourceIP,destIP):
	for i,p in enumerate(path):
		if "s" in p:# or i == len(path)-1:
			dpid=Network.node[p]['DPID']
			print "node:%s",p
			if (i+1) < len(path):
				nextHop = path[i+1]
				print "nexthop:%s",nextHop
			for i,interface in enumerate(Network.node[p]['interfaces']):
				L = Network.node[p]['interfaces'][i]['link']
				for i2,interface2 in enumerate(Network.node[nextHop]['interfaces']):
					print "nexthop interface:%s",Network.node[nextHop]['interfaces'][i2]['link']
					if (Network.node[nextHop]['interfaces'][i2]['link']== L):
						finalLink=L
#						print "node interface:%s",L
						print "final Link:%s", finalLink
							
'''

	flow = {
    		'switch':dpid,
    		"name":"flow_" + count,
		"cookie" : "0"
    		"priority":"3",
		"eth_type" : "0x0x800", 
    		"ipv4_src" : sourceIP,
		"ipv4_dst" : destIP,
    		"active":"true",
    		"actions":"set_eth_src=02:cd:3b:33:87:63,set_eth_dst=02:43:58:c8:59:43,output=2"
    		}
'''
for path in nx.all_simple_paths(Network, source='h2', target='h3'):
        if path not in nx.shortest_path(Network, source='h2', target='h3'):
		sendPath = path

sourceip=Network.node['h2']['interfaces'][0]['IP']
destip=Network.node['h3']['interfaces'][0]['IP']
generate_rule_for_path(sendPath,sourceip,destip)
'''
#---------get statistics-----------#

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
				L = Network.node[nodes]['interfaces'][i]['link']
				if (P <> 'local') and (L in interswitchLinks):
                			command = "curl http://%s/wm/statistics/bandwidth/'%s'/'%s'/json" % (controllerIp, Network.node[nodes]['DPID'],P)
                			result=os.popen(command).read()
                			parsedResult = json.loads(result)
                			for result in parsedResult:
						if (result['port'] == P):
							Bandwidth_t1[result['dpid']+result['port']] = int(result['bits-per-second-tx'])+int(result['bits-per-second-rx'])
	
	time.sleep(10)

#----------Query for stats at t2----------#

	for nodes in Network.nodes():
        	if Network.node[nodes]['DPID'] is not None:
                	for i,interface in enumerate(Network.node[nodes]['interfaces']):
                        	P =  Network.node[nodes]['interfaces'][i]['Port']
				L = Network.node[nodes]['interfaces'][i]['link']
                        	if (P <> 'local') and (L in interswitchLinks):
                                        command = "curl http://%s/wm/statistics/bandwidth/'%s'/'%s'/json" % (controllerIp, Network.node[nodes]['DPID'],P)
                                        result=os.popen(command).read()
                                        parsedResult = json.loads(result)
                                        for result in parsedResult:
						if (result['port'] == P):
							Bandwidth_t2[result['dpid']+result['port']] = int(result['bits-per-second-tx'])+int(result['bits-per-second-rx'])

#----------Calculate Bandwidth Difference----------#

	for nodes in Network.nodes():
                if Network.node[nodes]['DPID'] is not None:
                        for i,interface in enumerate(Network.node[nodes]['interfaces']):
                                P =  Network.node[nodes]['interfaces'][i]['Port']
				L = Network.node[nodes]['interfaces'][i]['link']
                                if (P <> 'local') and (L in interswitchLinks):
                                	BandwidthUsage[Network.node[nodes]['DPID']+P] = Bandwidth_t2[Network.node[nodes]['DPID']+P] - Bandwidth_t1[Network.node[nodes]['DPID']+P]

#	print BandwidthUsage	
	
'''
#-------Poll switches to see which flows are active-----#	
