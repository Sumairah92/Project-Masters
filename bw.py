'''
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
'''



'''
        for s in switchHostsFlows:
                command = "curl -s http://%s/wm/core/switch/'%s'/flow/json" % (controllerIp,s['dpid'])
                result=os.popen(command).read()
                parsedResult = json.loads(result)
                for flows in parsedResult['flows']:
                        if (flows['priority'] =='3'):
                                if ((flows['match']['ipv4_src'] == sourceIP) and (flows['match']['ipv4_dst'] == destIP)):
                                        return
'''
