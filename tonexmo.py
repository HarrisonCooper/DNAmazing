# -*- coding: utf-8 -*-
"""
Created on Sat Apr 29 11:53:46 2017

@author: Gemma
"""

import nexmo
import urllib
import urllib2
import json
#import DNAmazing.py ?


base_url = 'https://api.nexmo.com'
version = '/v1'

def makeclient():
    api_key=''
    api_secret=''
    #Need to get this from nexmo profile.
    client=nexmo.Client(key=api_key, secret=api_secret)
    return client

def buynumber():
    """Purchases number. But would bleed through money if we do this everytime?
        Might be best to purchase number and recursively modify data. Could 
        use this instead to couple the number information to the rest of the 
        data?"""
    pass

    

class Application(object):
    """Everything to do with applications. Could do:
        -Caller calls. 
        -Makes application based on their match information. 
        -Deletes applications (to avoid proliferation of lots of applications
         every time someone calls...)"""
    
    def __init__(self, name, descript):
        self.name=name
        #Name of application. E.g number of button press.
        self.description=descript
        #Description of what application does. E.g repeats options.
        
    def loadamazing():
        """Runs DNAmazing.py and gets output into a nice format. Need to send 
        this into update json."""
        pass

    def retrieve():
        #Could retrieve single application, or list of them using API? 
        #Not really sure what this does in the docs.....
        pass
    

class Event(object):
    #Creates events.
    pass


class Caller(object):
    
    def call():
        #Includes number being sent to, number being sent from and answer url.
        #Use client.create_call method ?
        pass

client=makeclient()
