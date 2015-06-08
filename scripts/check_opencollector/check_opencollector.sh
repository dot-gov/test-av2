#!/bin/bash

cd /root/collectors/
file=$(tempfile /tmp/c)

error=0

for ip in $( cat known_collectors.txt )
do
    echo PING: $ip
    hping3 $ip -S -c 3 -1
    if [ $? -eq 0 ]
    then
        echo PING $ip >> $file
        error=1
    fi
done

nmap -iL known_collectors.txt -oA $file -sS -P0 -O -sV -p 1,21,22,53,80,81,8080,135,139,445,3389,5800,5900,49154
grep open $file.gnmap >> $file && error=1

if [ $error -eq 1 ]
then
      for m in zeno@hackingteam.com alor@hackingteam.com fabio@hackingteam.com
        do cat $file | mail -s "CHECK COLLECTORS: ERROR" $m
      done

else
    for m in zeno@hackingteam.com
        do echo OK | mail -s "CHECK COLLECTORS: OK" $m
    done
fi

rm -f $file*

