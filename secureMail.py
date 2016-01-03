# Author: Anish Ramasekar
# Date Created: 11/29/2015

# !/usr/bin/python

import os
import urllib
import commands

mycertlist = dict()


def download_cert(certname):
    response = urllib.urlopen('https://courses.ncsu.edu/csc574/lec/001/CertificateRepo')

    html = response.readlines()

    for line in html:
        if certname in line:
            username, link = line.split(',')

    url, filename = link.rsplit('/', 1)

    filename = str(filename.strip("\n"))
    # print username
    # print link
    # print filename

    mycertlist[certname] = filename

    urllib.urlretrieve(link, filename)
    # print mycertlist
    return filename


def formatfile(snd, rxr):
    mail = ''
    mail += "from: " + snd + "@ncsu.edu, to: " + rxr + "@ncsu.edu\n"
    f = open('sendMail.txt', 'w')
    f.write(mail)
    f.close()
    os.system('sh createMail.sh')


def send_mail():
    print "Enter your unity id"
    sender = str(raw_input())

    print "Enter the message that you want to send"
    message = str(raw_input())

    print "Enter the recipients unity id"
    recipient = str(raw_input())

    if recipient in mycertlist:
        verifyfile = mycertlist[recipient].strip("'");
    else:
        verifyfile = download_cert(recipient)

    command = "openssl verify -CAfile root-ca.crt " + verifyfile
    cmdout = commands.getoutput(command);
    reqout = "" + verifyfile + ": OK"
    print cmdout
    print reqout
    if str(reqout) == str(cmdout):
        print "Success"

    # generate random pass-phrase using openssl
    os.system('openssl rand -base64 32 > sessionKey.txt')

    # generate the public key for the recipient
    cmd = 'openssl x509 -pubkey -noout -in ' + verifyfile + ' > public.pem'
    os.system(cmd)
    os.system('openssl rsautl -encrypt -inkey public.pem -pubin -in sessionKey.txt -out encryptedKey.txt')
    os.system('cat encryptedKey.txt | openssl enc -base64 > encryptedKey64.txt')

    with open('message.txt', 'w') as fout:
        fout.write(message)

    with open('keystore.txt', 'w') as file:
        file.write(str(mycertlist))

    file.close()
    fout.close()

    # encrypting message using session key
    os.system('openssl enc -aes-256-cbc -base64 -in message.txt -out encryptedMessage64.txt -pass file:sessionKey.txt')

    os.system('cat encryptedKey64.txt > final_file.txt')
    os.system('echo >> final_file.txt')
    os.system('cat encryptedMessage64.txt >> final_file.txt')

    print "Enter the name of the private key cert (.pem) required for signing "
    private_key = str(raw_input())

    # signature for the final content
    sign_cmd = "openssl dgst -sha1 -sign " + private_key + " -out final.txt.sha1 final_file.txt"
    os.system(sign_cmd)
    os.system('echo >> final.txt.sha1')
    os.system('cat final.txt.sha1 | openssl enc -base64 > final64.txt.sha1')
    formatfile(sender, recipient)
    os.system('sh sendClean.sh')


def receive_mail():
    isblank = 0
    count = 0
    print "Enter the name of the file "
    mail_file = str(raw_input())
    f = open(mail_file, 'r')
    dec_file = open('digital_sign64.txt.sha1', 'w')
    mysender = f.readline().split(":")[-2].split("@ncsu.edu")[-2].strip()
    print "Sender: " + mysender
    for line in f.readlines():
        if not line.strip():
            isblank += 1

        if isblank == 2:
            if not line.strip().startswith("-----END CSC574 MESSAGE-----") and line.strip():
                if count == 0:
                    dec_file.writelines(line.strip())
                    count = 1
                else:
                    dec_file.writelines("\n" + line.strip())

    dec_file.close()
    f.close()

    if mysender in mycertlist:
        verifyfile = mycertlist[mysender].strip("'");
    else:
        verifyfile = download_cert(mysender)

    command = "openssl verify -CAfile root-ca.crt " + verifyfile
    cmdout = commands.getoutput(command);
    reqout = "" + verifyfile + ": OK"
    print cmdout
    if str(reqout) == str(cmdout):
        print "Success - verified cert"

    # logic for printing senders email from certificate
    cat_command = "cat " + verifyfile + " | grep @ncsu.edu"
    sender_out = commands.getoutput(cat_command)
    print "Sender info from cert: " + sender_out.split("/emailAddress=")[-1].strip()

    read_flag = 0
    isblank = 0
    # create file to check signature
    input_file = open(mail_file, 'r')
    out_file = open('rec_sign_file.txt', 'w')
    for line in input_file.readlines():
        if not line.strip():
            isblank += 1

        if read_flag == 1 and isblank != 2:
            out_file.write(line.strip() + "\n")

        if isblank == 2:
            break

        if line.startswith("-----BEGIN CSC574 MESSAGE-----"):
            read_flag = 1

    out_file.close()
    input_file.close()

    # check if the signature is same
    cmd = 'openssl x509 -pubkey -noout -in ' + verifyfile + ' > public.pem'
    os.system(cmd)
    os.system('cat digital_sign64.txt.sha1 | openssl enc -base64 -d > digital_sign.txt.sha1')
    verify_cmd = "openssl dgst -sha1 -verify public.pem -signature digital_sign.txt.sha1 rec_sign_file.txt"
    sign_status = commands.getoutput(verify_cmd)
    print sign_status

    if sign_status == "Verified OK":
        print "Signature - VALID"

        line_count = 0
        f = open(mail_file, 'r')
        dec_file = open('dec_session_key64.txt', 'w')

        for line in f.readlines():
            line_count += 1

            if line_count == 3:
                dec_file.write(line.strip())

            if line_count > 3 and line.strip():
                dec_file.write("\n" + line.strip())

            if not line.strip():
                break

        dec_file.close()
        f.close()

        # print "Finished creating the decrypt file"
        print "Enter the name of private key cert(.pem) required for decryption "
        pri_key = str(raw_input())
        dec_cmd = "openssl rsautl -inkey " + pri_key + " -decrypt -in dec_session_key.txt -out decrypt_key.txt"
        os.system('cat dec_session_key64.txt | openssl enc -base64 -d > dec_session_key.txt')
        os.system(dec_cmd)

        f = open(mail_file, 'r')
        msg_file = open('rec_msg64.txt', 'w')
        isblank = 0
        line_count = 0
        for line in f.readlines():
            if isblank == 1 and line.strip():
                if line_count == 0:
                    msg_file.write(line.strip())
                    line_count += 1
                else:
                    msg_file.write("\n" + line.strip())
                    line_count += 1

            if not line.strip():
                if isblank == 0:
                    isblank = 1
                else:
                    break

        f.close()
        msg_file.close()

        os.system('echo >> rec_msg64.txt')

        session_key = ""
        sessionfile = open('decrypt_key.txt', 'r')
        for line in sessionfile.readline():
            session_key += line.strip()

        sessionfile.close()

        print "Message:"
        finalcmd = "openssl enc -aes-256-cbc -d -base64 -in rec_msg64.txt -k " + session_key
        os.system(finalcmd)
        os.system('echo')
    else:
        print "Signature does not match"

    os.system('sh cleanUp.sh')

    with open('keystore.txt', 'w') as cert_out:
        cert_out.write(str(mycertlist))


if os.path.isfile('keystore.txt'):
    fread = open('keystore.txt', 'r')
    mycertlist = eval(fread.read())
print "Enter 1 to send mail "
print "Enter 2 to receive a mail "
print "Enter 3 to print contents of database "
choice = int(raw_input())
if choice == 1:
    send_mail()
elif choice == 2:
    receive_mail()
else:
    for item in mycertlist:
        print item, mycertlist[item]
