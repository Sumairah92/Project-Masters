import os
import json
import io
import time
import untangle
import networkx as nx

controllerIp = '128.163.232.72:8080'
dpids = list()

#build topology
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

interfaces = list()
links = list()
obj = untangle.parse("topology.xml")
for link in obj.rspec.link:
	for interface in link.interface_ref:
		I = {'interface': interface["client_id"],'name':link["client_id"]}
		links.append(I)

for node in obj.rspec.node:
	if node["client_id"]<>'GDGN0' and node["client_id"]<>'AAGCTRL0':
        	Network.add_node(node["client_id"])
        	for interface in node.interface:
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
		 'DPID' : dp}

    	Network.add_node(host['name'], interfaces=host['interfaces'], DPID = host['DPID'])
    	interfaces= []
	dp = None

print Network.nodes(data=True)
'''e=('s1','s2')
Network.add_edge(*e)
e=('s2','s3')
Network.add_edge(*e)
e=('s3','s1')
Network.add_edge(*e)
e=('s1','h1')
Network.add_edge(*e)
e=('s2','h2')
Network.add_edge(*e)
e=('s3','h3')
Network.add_edge(*e)
'''
#Network.node['s1']['DPIP'] = 'x:00:00:00:00'
#print Network.nodes(data=True)
#for path in nx.all_simple_paths(Network, source='s1', target='h1'):
#    print (path)

#get statistics

#enable statistics in the switches

#command = "curl -X POST -d '' http://%s/wm/statistics/config/enable/json" % controllerIp
#os.popen(command).read()
command = "curl http://%s/wm/statistics/bandwidth/\"all\"/\"all\"/json" % controllerIp
result=os.popen(command).read()
parsedResult = json.loads(result)
'''for result in parsedResult:
    print "DPID: %s" % result['dpid']
    print "bits-per-second-rx: %s" % result['bits-per-second-rx']
    print "bits-per-second-tx: %s" %result['bits-per-second-tx']
#add route
'''
