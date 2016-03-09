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
d = dict()
interfaces = list()
links = list()
obj = untangle.parse("topology.xml")
for node in obj.rspec.node:
    if node["client_id"]<>'GDGN0' and node["client_id"]<>'AAGCTRL0':
        Network.add_node(node["client_id"])
        for interface in node.interface:
            I = { 'name' : interface["client_id"],
                  'IP' : interface.ip["address"]}
            interfaces.append(I)
    host = { 'name' : node["client_id"],
         'interfaces' : interfaces}
    Network.add_node(host['name'], interfaces=host['interfaces'])
    interfaces= []
'''
for link in obj.rspec.link:
    print link["client_id"]
    for interface in link.interface_ref:
        print interface["client_id"]
'''




print Network.nodes(data=True)






e=('s1','s2')
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
#for path in nx.all_simple_paths(Network, source='s1', target='h1'):
#    print (path)

'''
# Get switch and link information from the controller
#maybe use curl http://128.163.232.72:8080/wm/core/switch/all/desc/json and other parameters check
command = "curl -s http://%s/wm/core/controller/switches/json" % controllerIp
result = os.popen(command).read()
parsedResult = json.loads(result)
print parsedResult
for result in parsedResult:
# print result['switchDPID']
    Network.add_node(result['switchDPID'], address=result['inetAddress'])
#print Network.nodes(data=True)
#get statistics

#enable statistics in the switches

#command = "curl -X POST -d '' http://%s/wm/statistics/config/enable/json" % controllerIp
#os.popen(command).read()
command = "curl http://%s/wm/statistics/bandwidth/\"all\"/\"all\"/json" % controllerIp
result=os.popen(command).read()
parsedResult = json.loads(result)
for result in parsedResult:
    print "DPID: %s" % result['dpid']
    print "bits-per-second-rx: %s" % result['bits-per-second-rx']
    print "bits-per-second-tx: %s" %result['bits-per-second-tx']
#add route
'''
