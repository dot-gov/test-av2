#!/bin/sh

cd /home/avmonitor/certs/
file=$(tempfile /tmp/p)

for cert in xx.pem ma.pem me.pem
do
    echo CERT: $cert
    cat $cert | grep friendlyName | uniq > $file
    openssl ocsp -issuer certum.1.int.cer -cert $cert -url http://ocsp.certum.pl >> $file 2> /dev/null

    good=$(cat $file | grep $cert)

    echo $good
    #echo $file

    cat $file | mail -s "CHECKCERT: $good" zeno@hackingteam.com

    if [ -z "$(grep good $file)" ]
    then
      for m in zeno@hackingteam.com alor@hackingteam.it
      #for m in zeno@hackingteam.com
        do cat $file | mail -s "CHECKCERT: $good" $m
      done
    fi

    rm $file

done