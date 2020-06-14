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
