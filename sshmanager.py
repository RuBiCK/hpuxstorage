#!/usr/bin/env python
#from paramiko import SSHClient
from paramiko import AutoAddPolicy
import paramiko

keypriv ='id_rsa'

class Con_manager(paramiko.SSHClient):
    def open_con(self,host):
	try:
       		self.set_missing_host_key_policy(AutoAddPolicy())
        	self.connect( host, key_filename=keypriv)
	except:
        	print "Error connecting to host " + host

    def run(self,cmd,mode=''):
	#run function will return by default a list if mode no specified. if mode=s return string for one line
	stdin, stdout, stderr = self.exec_command(cmd)
	if mode == '':
		salida =stdout.readlines()
	elif mode == 's':
		salida = stdout.readline()
		salida = salida.rstrip('\n')
	return salida

    def close_con(self):
	self.close()
