#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup
import hashlib

host = 'docker.hackthebox.eu'
port = 32648

def md5hash(my_string):
    m = hashlib.md5()
    m.update(my_string.encode('utf-8'))
    return m.hexdigest()

with requests.Session() as s:
	# get hash
	html = s.get('http://{}:{}'.format(host, port))
	#print(html.text)
	soup = BeautifulSoup(html.text, 'html.parser')

	# compute md5
	h = soup.h3.string
	md5 = md5hash(h)
	#print("[*] hash={} md5={}".format(h, md5))

	# post value
	data = {"hash":md5, "submit":"Submit"}
	html = s.post('http://{}:{}'.format(host, port), data=data)
	soup = BeautifulSoup(html.text, 'html.parser')
	print(soup.p.string)