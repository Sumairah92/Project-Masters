import os
import json
import io
import time
import untangle
import time
import re
import networkx as nx

B_t1 = dict()
B_t2 = dict()
bandwidth = dict()

B_t1 = { '00:80'+'1' : 1000,
	'00:50'+'1': 0,
	'00:80'+'2':300,
	'00:50'+'2':100}

B_t2 = { '00:80'+'1' : 2000,
        '00:50'+'1': 10,
        '00:80'+'2':200,
        '00:50'+'2':100}
bandwidth={ '00:80'+'1' : B_t2['00:801']-B_t1['00:801'],
        '00:50'+'1': B_t2['00:501']-B_t1['00:501'],
        '00:80'+'2':B_t2['00:802']-B_t1['00:802'],
        '00:50'+'2':B_t2['00:502']-B_t1['00:502']}
print bandwidth
