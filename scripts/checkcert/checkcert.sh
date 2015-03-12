#!/bin/sh

# to convert a pfx in pem:
# openssl pkcs12 -in certificate.pfx -out certificate.pem -nodes

cd /home/avmonitor/certs/
file=$(tempfile /tmp/p)

rm toZeno.mail 2> /dev/null

error="OK"
for cert in xx.pem ma.pem me.pem mt.pem mw.pem
do
  echo CERT: $cert
  cat $cert | grep friendlyName | uniq > $file
  openssl ocsp -issuer certum.1.int.cer -cert $cert -url http://ocsp.certum.pl >> $file 2> /dev/null

  good=$(cat $file | grep $cert)

  echo $good
  #echo $file

  cat $file >> toZeno.mail
  echo "---------------" >> toZeno.mail
  # | mail -s "CHECKCERT: $good" zeno@hackingteam.com

  if [ -z "$(grep good $file)" ]
  then
    error="ERRORS"
    for m in zeno@hackingteam.com alor@hackingteam.com f.busatto@hackingteam.com
      do cat $file | mail -s "CHECK CERT: $good" $m
      #do cat $file
    done
  fi

  rm $file
done

cat toZeno.mail | mail -s "CHECK CERT $error" zeno@hackingteam.com