#!bin/bash

echo "-----BEGIN CSC574 MESSAGE-----" >> sendMail.txt
cat encryptedKey64.txt >> sendMail.txt
echo >> sendMail.txt
cat encryptedMessage64.txt >> sendMail.txt
echo >> sendMail.txt
cat final64.txt.sha1 >> sendMail.txt
echo "-----END CSC574 MESSAGE-----" >> sendMail.txt