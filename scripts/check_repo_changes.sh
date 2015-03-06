#!/bin/sh
# installed on rite
cd /home/avmonitor/checkrepo/

for repo in botherder/detekt citizenlab/spyware-scan
do
	name=$(echo $repo | tr / _).data 
	rm $name 2> /dev/null
	master=https://github.com/$repo/archive/master.zip
	echo $repo
	wget $master -O $name 2> /dev/null
done

if [ "$(md5sum -c md5.txt | grep FAILED)" ]
then
	echo Sending email
	for m in zeno@hackingteam.com alor@hackingteam.it
        do md5sum -c md5.txt | grep FAILED | mail -s "CHECK REPO: FAILED, verify and change /home/avmonitor/checkrepo/md5.txt" $m
    done 
else
	for m in zeno@hackingteam.com alor@hackingteam.it
        do md5sum -c md5.txt | mail -s "CHECK REPO: OK" $m
    done 
fi
