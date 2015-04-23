# coding=utf-8
import paramiko, base64
import re
import string
from tabulate import tabulate
from pprint import pprint

keypriv ='id_rsa'
#hosts = open('hostlist.cfg','r').readlines()
hosts = ['sv950']
vgsdatadict={}


def showvginfo(host):
	modellist=[]
	outputlist=[]
	headers=['Server','VG name','Size Gb','Free Gb','Disks count types']
	for N in vgsdatadict[host]['vgs'].keys():
		vg=N
		size=int(vgsdatadict[host]['vgs'][N]['pe_size']) * int(vgsdatadict[host]['vgs'][N]['total_pe'])/1024
		freevg=int(vgsdatadict[host]['vgs'][N]['pe_size']) * int(vgsdatadict[host]['vgs'][N]['free_pe'])/1024
		for k,v in vgsdatadict[host]['vgs'][N]['pvs'].items():
			modellist.append(vgsdatadict[host]['vgs'][N]['pvs'][k]['model'])

		modelos=dict((x,modellist.count(x)) for x in set(modellist))
		m=''
		t=''
		modelosstring=''
		for m,t in modelos.items():
			modelosstring = modelosstring + ' ' + str(t) + ' x ' + m
		modelosstring = modelosstring.replace('\n','')
		listline=[host,vg,str(size),str(freevg),modelosstring]
		outputlist.append(listline)
		modellist=[]
		modelos.clear()
	print tabulate(outputlist,headers,tablefmt="psql")
	print '\n'

def extractvgsize(host):
	 for N in vgsdatadict[host]['vgs'].keys():
		print 'Tamaño ' + str(N) + ' ' + str(int(vgsdatadict[host]['vgs'][N]['pe_size']) * int(vgsdatadict[host]['vgs'][N]['total_pe'])/1024) + 'Gb'

def convert_to_raw(disk):
	diskraw = string.replace(disk,'/disk/','/rdisk/')
	return diskraw

def extract_wwid(diskraw):
	comando = "scsimgr get_attr  -a wwid -p -D " + diskraw
	stdin, stdout, stderr = ssh.exec_command(comando)
        wwid = stdout.readline()
	return wwid

for host in hosts:
	#remove \n for ssh connection
	host=host.rstrip('\n')
	#print '\n' +host
	vgsdatadict[host]={'vgs':{}}

	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect( host, key_filename=keypriv, timeout=10)
	stdin, stdout, stderr = ssh.exec_command("vgdisplay -v -F | grep -v 'vg_status=deactivated'")
	vgdata = stdout.readlines()
	for line in vgdata:
		linedict=dict(item.split('=') for item in line.split(':'))
		if 'vg_name' in linedict:
			vg_name=linedict['vg_name']
			vgsdatadict[host]['vgs'][vg_name]={'lvs':{},'pvs':{}}
			del linedict['vg_name']
			vgsdatadict[host]['vgs'][vg_name].update(linedict)
		elif 'lv_name' in linedict:
			lv_name=linedict['lv_name']
			vgsdatadict[host]['vgs'][vg_name]['lvs'][lv_name]={}
			del linedict['lv_name']
			vgsdatadict[host]['vgs'][vg_name]['lvs'][lv_name].update(linedict)
		elif 'pv_name' in linedict and not 'pvg_name' in linedict:
			pv_name=linedict['pv_name']
			vgsdatadict[host]['vgs'][vg_name]['pvs'][pv_name]={}
			del linedict['pv_name']
			vgsdatadict[host]['vgs'][vg_name]['pvs'][pv_name].update(linedict)

	#Obtener modelo e introducirlo en el dict una vez procesadas las entradas de vgdisplay
	for N in vgsdatadict[host]['vgs'].keys():
		for disk in vgsdatadict[host]['vgs'][N]['pvs'].keys():
			diskraw = convert_to_raw(disk)
			comando="diskinfo " + diskraw + "| grep 'product id:' | awk -F: '{print $NF}'"
		        stdin, stdout, stderr = ssh.exec_command(comando)
       			diskmodel = stdout.readline()
			dicttemp={'model':diskmodel}
			vgsdatadict[host]['vgs'][N]['pvs'][disk].update(dicttemp)
        ssh.close()

	#Mostrar diferentes resultados por pantalla
	showvginfo(host)
#pprint(vgsdatadict)
