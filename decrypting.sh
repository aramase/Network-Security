#!/bin/bash

for first in {a..z}; do
for second in {a..z}; do
for third in {a..z}; do

STR=$first$second$third

openssl enc -d -des-cbc -base64 -in outfile.txt -k $STR -out infile-"$STR".txt &> baderror.txt

if grep -q "bad decrypt" baderror.txt; then
	rm baderror.txt
	rm infile-"$STR".txt
else
	if LC_ALL=C grep -q '[^ -~]' infile-"$STR".txt; then
    	rm baderror.txt
    	rm infile-"$STR".txt
    else
    	rm baderror.txt
	fi
fi

done
done
done