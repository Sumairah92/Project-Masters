import untangle
def main():
#make some changes to check git push	
	obj = untangle.parse("topology.xml")
	#obj.rspec.link[0]["client_id"]
#	for child in obj.rspec:
#		print(child)
	for node in obj.rspec.node:
		print(node["client_id"])
		if node.interface:
			for interface in node.interface:
				print(interface["client_id"])
				print(interface.ip["address"])
		
main()
