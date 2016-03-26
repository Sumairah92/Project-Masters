import os
import json
import io
import time
import untangle
import time
import re
import networkx as nx

#Declare variables

controllerIp = '150.182.135.41:8080'
dpids = list()
edges = list()
interfaces = list()
links = list()
interswitchLinks = list()
Network = nx.Graph()
Bandwidth_t1 = dict()
switchHostsFlows=list()

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

#-------Make list of host IPs connected to switches------------#
for d in dpids:
        command = "curl -s http://%s/wm/core/switch/'%s'/flow/json" % (controllerIp,d)
        result=os.popen(command).read()
        parsedResult = json.loads(result)
        for nodes in Network.nodes():
                if Network.node[nodes]['DPID'] == d:
                        for i,interface in enumerate(Network.node[nodes]['interfaces']):
                                ip=Network.node[nodes]['interfaces'][i]['IP']
				port=Network.node[nodes]['interfaces'][i]['Port']
                                for flows in parsedResult['flows']:
                                        if (flows['priority'] == '1'):
                                                hostIp=flows['match']['ipv4_src']
						dstIp=flows['match']['ipv4_dst']
                                                if (hostIp[:-2] == ip[:-2]):
							for nodes2 in Network.nodes():
								 for i2,interface2 in enumerate(Network.node[nodes2]['interfaces']):
									if (Network.node[nodes2]['interfaces'][i2]['IP']== hostIp):
										hostName=nodes2
									if (Network.node[nodes2]['interfaces'][i2]['IP']== dstIp):
										dstName=nodes2
                                                        I = {'switchName':nodes,
                                                              'host':hostIp,
							      'hostName':hostName,
							      'dst':dstIp,
							      'dstName':dstName,
                                                              'dpid': d,
							      'lastFlowHit':flows['packetCount']}
                                                        switchHostsFlows.append(I)
                                                        
#print Network.nodes(data=True)
#print switchHostsFlows
								

print "Topology created"
count = 0

def calculate_bandwidth_for_paths(src,tgt):
	pathBW = dict()
	paths = nx.all_simple_paths(Network, source=src, target=tgt)
	for num,path in enumerate(paths):
        	if path <> nx.shortest_path(Network, source=src, target=tgt):
			for i,hop in enumerate(path):
				if "s" in hop:
					dpid=Network.node[hop]['DPID']
					if (i+1) < len(path)-1:
						nextHop = path[i+1]
						for x,interface in enumerate(Network.node[hop]['interfaces']):
							L = Network.node[hop]['interfaces'][x]['link']
							for x2,interface2 in enumerate(Network.node[nextHop]['interfaces']):
								if (Network.node[nextHop]['interfaces'][x2]['link'] == L):		
									port = Network.node[hop]['interfaces'][x]['Port']
		#				print num,dpid,port,Bandwidth_t1[dpid+port]
	#					pathBW +=  Bandwidth_t1[dpid+port]
	for path in paths:
		print path
		
						
						

def generate_rule_for_path(path,sourceIP,destIP):
	for s in switchHostsFlows:
		command = "curl -s http://%s/wm/core/switch/'%s'/flow/json" % (controllerIp,s['dpid'])
		result=os.popen(command).read()
                parsedResult = json.loads(result)
		for flows in parsedResult['flows']:
                        if (flows['priority'] =='3'):
                                if ((flows['match']['ipv4_src'] == sourceIP) and (flows['match']['ipv4_dst'] == destIP)):
					return
	flowList = list()
	global count
	for i,p in enumerate(path):
		if "s" in p:# or i == len(path)-1:
			dpid=Network.node[p]['DPID']
			if (i+1) < len(path):
				nextHop = path[i+1]
			for i,interface in enumerate(Network.node[p]['interfaces']):
				L = Network.node[p]['interfaces'][i]['link']
				for i2,interface2 in enumerate(Network.node[nextHop]['interfaces']):
					if (Network.node[nextHop]['interfaces'][i2]['link']== L):
						finalLink = L
						ethsrc = Network.node[p]['interfaces'][i]['MAC']
						ethdst = Network.node[nextHop]['interfaces'][i2]['MAC']
						port = Network.node[p]['interfaces'][i]['Port']
		
						flow = {
    							'switch':dpid,
    							"name":"flow_" + str(count),
							"cookie":"0",
    							"priority":"3",
							"eth_type":"0x0800", 
    							"ipv4_src":sourceIP,
							"ipv4_dst":destIP,
							 "idle_timeout":"60",
    							"active":"true",
    							"actions":"set_eth_src="+ethsrc+",set_eth_dst="+ethdst+",output="+port
    							}
						count += 1
						flowList.append(flow)
	for flow in flowList:
		f = json.dumps(flow,separators=(',', ':'))
		command = "curl -X POST -d '"+f+"' http://%s/wm/staticflowpusher/json" % controllerIp
		print command
#		result=os.popen(command).read()
#		print result
		
#calculate_bandwidth_for_paths('h3','h4')
'''for path in nx.all_simple_paths(Network, source='h2', target='h3'):
        if path not in nx.shortest_path(Network, source='h2', target='h3'):
		sendPath = path

sourceip=Network.node['h2']['interfaces'][0]['IP']
destip=Network.node['h3']['interfaces'][0]['IP']
generate_rule_for_path(sendPath,sourceip,destip)
sendPath = nx.shortest_path(Network, source = 'h4', target = 'h3')
print sendPath
sourceip=Network.node['h4']['interfaces'][0]['IP']
destip=Network.node['h3']['interfaces'][0]['IP']
generate_rule_for_path(sendPath,sourceip,destip)
'''
#---------get statistics-----------#

print "Preparing for querying statistics"
#time.sleep(5)


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
							Bandwidth_t1[result['dpid']+result['port']] = 100000000-(int(result['bits-per-second-tx'])+int(result['bits-per-second-rx']))
#	print Bandwidth_t1	
	time.sleep(5)
	calculate_bandwidth_for_paths('h3','h4')

#-------Poll switches to see which flows are active-----#	
'''
	for s in switchHostsFlows:
		command = "curl -s http://%s/wm/core/switch/'%s'/flow/json" % (controllerIp,s['dpid'])
		result=os.popen(command).read()
        	parsedResult = json.loads(result)				
		for flows in parsedResult['flows']:
			if (flows['priority'] =='1'):
                		if (flows['match']['ipv4_src'] in s['host'] and flows['match']['ipv4_dst'] in s['dst']):
					if (s['lastFlowHit'] == flows['packetCount']):
						print "Polling"
					else:
						s['lastFlowHit'] = flows['packetCount']
						#Get bandwidth
#						for path in nx.all_simple_paths(Network, source=s['hostName'], target=s['dstName']):
#        						if path <> nx.shortest_path(Network, source=s['hostName'], target=s['dstName']):
#								sendPath = path

						sourceip=s['host']
						destip=flows['match']['ipv4_dst']
#						calculate_bandwidth_for_paths(s['hostName'],s['dstName'])
#						print sendPath,sourceip,destip
#						generate_rule_for_path(sendPath,sourceip,destip)
'''			
