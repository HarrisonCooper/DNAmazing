# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 07:09:27 2017

@author: Gemma
"""

import smtplib
import numpy as np
import base64

smtpObj=smtplib.SMTP('smtp.gmail.com', 587)
#Connects to gmail server.
smtpObj.ehlo()
smtpObj.starttls()

usermail='dnamazing.report@gmail.com'
userpass='dnamazing_hackmed17'
mailto='hpcooper1@sheffield.ac.uk'
#mailto='thebrickmaster@theratefamily.co.uk'
marker = "AUNIQUEMARKER"

attachfile='./test.csv'

# Read a file and encode it into base64 format
fo = open(attachfile, "rb")
filecontent = fo.read()
encodedcontent = base64.b64encode(filecontent)  # base64

#Will be passed from command line later.

smtpObj.login(usermail, userpass)
#Logs in to our email address.

subjectstr='Subject: MRSA detection report. \n'
#Creates string for sub

output=[1, 2, 3, 4, 5, 6, 7, 8]
#Will be passed from ARAlert output.

samplename='test'

if len(output)>0:
    bodystr=('Dear user,\n\nWarning, resistances to the following drugs were '
             'detected in sample ' + samplename+':\n\n')
    #Creates strings for body of the email.
    for resistance in output:
        linestr=str(resistance)+'\n'
        bodystr=bodystr+linestr
else:
    bodystr='Dear user,\n\nNo resistances were detected in sample' + samplename+'.\n'

bodystr=(bodystr+'\n\n The DNAmazing team\n\nContact us at: '+usermail)


# Define the attachment section
attachment = """Content-Type: multipart/mixed; name=\"%s\"
Content-Transfer-Encoding:base64
Content-Disposition: attachment; attachfile=%s

%s
--%s--
""" %(attachfile, attachfile, encodedcontent, marker)


smtpObj.sendmail(usermail, mailto, subjectstr+bodystr+attachment)
#Sends email.

smtpObj.quit()
#Disconnects from smtp server.
