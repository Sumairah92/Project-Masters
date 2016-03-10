import os
import json
import io
import time
import untangle
import networkx as nx

#Declare variables

controllerIp = '128.163.232.72:8080'
dpids = list()
edges = list()
interfaces = list()
links = list()
Network = nx.Graph()


# Get switch and link information from the controller
command = "curl -s http://%s/wm/core/controller/switches/json" % controllerIp
result = os.popen(command).read()
parsedResult = json.loads(result)
for result in parsedResult:
        d = result['switchDPID']
        dpids.append(d)


command = "curl -s http://%s//wm/core/switch/all/desc/json" % controllerIp
result = os.popen(command).read()
parsedResult = json.loads(result)


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
            		I = { 'name' : interface["client_id"],
                  		'IP' : interface.ip["address"],
			       'link' : thisLink}
            		interfaces.append(I)
		for d in dpids:
        		if parsedResult[d]['desc']['datapathDescription'] == node["client_id"]:
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
#print Network.edges(data=True)
for path in nx.all_simple_paths(Network, source='h2', target='h3'):
    print path

#get statistics

#enable statistics in the switches

#command = "curl -X POST -d '' http://%s/wm/statistics/config/enable/json" % controllerIp
#os.popen(command).read()
'''command = "curl http://%s/wm/statistics/bandwidth/\"all\"/\"all\"/json" % controllerIp
result=os.popen(command).read()
parsedResult = json.loads(result)
for result in parsedResult:
    print "DPID: %s" % result['dpid']
    print "bits-per-second-rx: %s" % result['bits-per-second-rx']
    print "bits-per-second-tx: %s" %result['bits-per-second-tx']
#add route
'''
