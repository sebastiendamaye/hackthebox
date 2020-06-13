# Baby RE

Let's unzip the file:

~~~
unknown@localhost:/data/downloads$ 7z x Baby_RE.zip 

7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,8 CPUs Intel(R) Core(TM) i7-4800MQ CPU @ 2.70GHz (306C3),ASM,AES-NI)

Scanning the drive for archives:
1 file, 2885 bytes (3 KiB)

Extracting archive: Baby_RE.zip
--
Path = Baby_RE.zip
Type = zip
Physical Size = 2885

    
Enter password (will not be echoed):
Everything is Ok

Size:       16760
Compressed: 2885
~~~

We have to deal with a Linux executable:

~~~
unknown@localhost:/data/downloads$ file baby 
baby: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=25adc53b89f781335a27bf1b81f5c4cb74581022, for GNU/Linux 3.2.0, not stripped
~~~

Make it executable and run it:

~~~
unknown@localhost:/data/downloads$ ./baby 
Insert key: 
oops
Try again later.
~~~

Let's use ltrace to check what it does:

~~~
unknown@localhost:/data/downloads$ ltrace ./baby 
puts("Insert key: "Insert key: 
)                             = 13
fgets(oops
"oops\n", 20, 0x7f0f605e57e0)              = 0x7ffcd694bb50
strcmp("oops\n", "abcde122313\n")                = 14
puts("Try again later."Try again later.
)                         = 17
+++ exited (status 0) +++
~~~

We see that the program calls `strcmp` to compare the user input with the expected string (`abcde122313`). Let's enter the correct string:

~~~
unknown@localhost:/data/downloads$ ./baby 
Insert key: 
abcde122313
HTB{B4BY_R3V_TH4TS_EZ}
~~~

Flag: `HTB{B4BY_R3V_TH4TS_EZ}`