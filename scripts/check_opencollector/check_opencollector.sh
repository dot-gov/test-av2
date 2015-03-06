#!/bin/bash
cat blacklist.txt known_collectors.txt > all.txt

flags="-P0 -O -sV -sC --osscan-guess -p 139,80,22,1"
nmap -iL all.txt --excludefile known_vps.txt $flags -oA nmap_results

xmllint --xpath '//port[@portid="80"]/state[@state="open"]/../service[@product="nginx"]/../../../os/osmatch[contains(@name,"Windows")]/../../address[@addr]' nmap_results.xml > addreses.xml

#grep -Fxvf known_vps.txt blacklist.txt known_collectors.txt | cut -d: -f2 | sort -n > all.txt
# grep -Fxf known_vps.txt blacklist.txt known_collectors.txt | sort -n
#for b in $all
#do
#    nmap $b $flags results/$b
#    xmllint --xpath '//state[@state="open"]/../../port[@portid="80"]' nmap_results.xml
#    xmllint --xpath '//port[@portid="80"]/state[@state="open"]' nmap_results.xml
#    xmllint --xpath '//port[@portid="80"]/state[@state="open"]/../service[@product="nginx"]/../../../os/osmatch[contains(@name,"Windows")]' results.xml
#done

xmllint --xpath '//port[@portid="80"]/state[@state="open"]/../../../os/osmatch[contains(@name,"Windows") and @accuracy > 90]/../../address[@addr]/' nmap_results.xml

