# coding=utf-8
from sshmanager import *
import re
import string
from tabulate import tabulate
from pprint import pprint

keypriv ='id_rsa'
#hosts = open('hostlist.cfg','r').readlines()
hosts = ['sv950','sv144','vh055']
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

		print modellist.count()
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

def is_hpivm():
	typeivm=str(mycon.run('/opt/hpvm/bin/hpvminfo','s'))
	print host
	if 'Running inside an HPVM guest' in typeivm:
		hpivm='guest'
	elif 'Running on an HPVM host' in typeivm:
		hpivm='host'
	else:
		hpivm='False'
	return hpivm

def extract_hpivmhost():
	command= "/opt/hpvm/bin/hpvminfo -V -S | awk '/hostname/ {print $NF}'"
        ivmhost=mycon.run(command,'s')
	return ivmhost

def extract_wwid(diskraw):
	command = "scsimgr get_attr  -a wwid -p -D " + diskraw
	wwid = mycon.run(command,'s')
	return wwid

def extract_vgdata():
	vgdata = mycon.run("vgdisplay -v -F | grep -v 'vg_status=deactivated'")
	for line in vgdata:
		linedict=dict(item.split('=') for item in line.split(':'))
		print linedict
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

def extract_pvmodel():
	#Extract for a given host, for each vg, all pv disk models
	for N in vgsdatadict[host]['vgs'].keys():
		for disk in vgsdatadict[host]['vgs'][N]['pvs'].keys():
			diskraw = convert_to_raw(disk)
			diskmodel=mycon.run("diskinfo " + diskraw + "| grep 'product id:' | awk -F: '{print $NF}'",'s')
			dicttemp={'model':diskmodel}
			vgsdatadict[host]['vgs'][N]['pvs'][disk].update(dicttemp)
		
			#Add wwid key-value for each disk
			dicttemp={'wwid':extract_wwid(diskraw)}
                        vgsdatadict[host]['vgs'][N]['pvs'][disk].update(dicttemp)

# ----------------------- MAIN ------------------------------
for host in hosts:
	#All functions that need connect to a server will use the variable 'host' to execute the commands on remote system
	#remove \n for ssh connection
	host=host.rstrip('\n')
	vgsdatadict[host]={}
	vgsdatadict[host]['vgs']={}
	mycon = Con_manager()
	mycon.open_con(host)
	hpivmtype = is_hpivm()
	if hpivmtype == 'host':
		vgsdatadict[host]['hpivm']='host'
	elif hpivmtype == 'guest':
		hpivmhost = extract_hpivmhost()
		vgsdatadict[host]['hpivm']='guest'
		vgsdatadict[host]['hpivmhost']=hpivmhost
	else:
		#Is string False because is not boolean (guest,host or False)
		vgsdatadict[host]['hpivm']='False'


	extract_vgdata()


	#Obtener modelo e introducirlo en el dict una vez procesadas las entradas de vgdisplay
	extract_pvmodel()

	#Mostrar diferentes resultados por pantalla
	#showvginfo(host)
	mycon.close()
pprint(vgsdatadict)
