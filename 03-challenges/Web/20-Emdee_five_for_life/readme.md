# Emdee five for life

When we connect to the "instance" generated randomly when we click on the "Start Instance" button, we see have a web page with a form. It is about MD5 hashing a string provided by the program. If the response is not provided fast enough, an error message (Too slow) will be displayed, and another string will be displayed.

```
$ curl -s http://docker.hackthebox.eu:32648/
<html>
<head>
<title>emdee five for life</title>
</head>
<body style="background-color:powderblue;">
<h1 align='center'>MD5 encrypt this string</h1><h3 align='center'>h3K0xOt2iZ2n6z2h4trJ</h3><center><form action="" method="post">
<input type="text" name="hash" placeholder="MD5" align='center'></input>
</br>
<input type="submit" value="Submit"></input>
</form></center>
</body>
</html>
```

You need to script it. It's quite basic, the only tricky part is that you have to create a session and make sure you post the response within the same session as the one that gave the challenge.

# python

Below is a possible answer in python.

```python
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
	soup = BeautifulSoup(html.text, 'html.parser')

	# compute md5
	h = soup.h3.string
	md5 = md5hash(h)

	# post value
	data = {"hash":md5, "submit":"Submit"}
	html = s.post('http://{}:{}'.format(host, port), data=data)
	soup = BeautifulSoup(html.text, 'html.parser')
	print(soup.p.string)
```

Once executed, the script will output the flag:

~~~
$ python script.py 
HTB{N1c3_ScrIpt1nG_B0i!}
~~~

# Shell

```bash
#!/bin/sh

# params
HOST="docker.hackthebox.eu"
PORT="32665"

# Get hash
HASH=$(curl -s -c cookie.txt http://$HOST:$PORT | grep -o "<h3 align='center'>.*</h3>" | sed -n 's/<h3.*>\(.*\)<\/h3>/\1/ip;T;q')

# compute md5
MD5="$(echo -n "$HASH" | md5sum | cut -d ' ' -f 1 )"

# post response
curl -s -b cookie.txt -d "hash=$MD5&submit=Submit" -X POST http://$HOST:$PORT | grep -o "<p align='center'>.*</p>" | sed -n 's/<p.*>\(.*\)<\/p>/\1/ip;T;q'
```

Output:

~~~
$ sh script.sh 
HTB{N1c3_ScrIpt1nG_B0i!}
~~~

# Flag
Flag: `HTB{N1c3_ScrIpt1nG_B0i!}`
