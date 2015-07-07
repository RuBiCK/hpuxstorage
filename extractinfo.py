#/usr/bin/python
# coding=utf-8
from sshmanager import *
import csv
import re
import string
import sys
import os
import inspect
from tabulate import tabulate
from pprint import pprint

keypriv ='id_rsa'
exportpath='/tmp/'
hosts = open('hostlist.cfg','r').readlines()
#hosts = ['sv950','vh056','sv144']

write_vginfo_header = 0
write_hpimvinfo = 0
#--------------- Functions -----------------

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

        if output == 'csv':
		print "dentro csv vginfo"
		global write_vginfo_header
		if write_vginfo_header == 0:
	                write_csv(headers, exportpath + "showvginfo.csv")
			write_vginfo_header = 1

                write_csv(outputlist, exportpath + "showvginfo.csv")

        else:
		print "else sin csv showvginfo"
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

def extract_vgdata(host):
	#host parameter not used
	vgdata = mycon.run("vgdisplay -v -F | grep -v 'vg_status=deactivated'")
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
def extract_disksize(host,diskraw):
	disksize=mycon.run("diskinfo -b " + diskraw,'s')
	return disksize

def extract_diskmodel(host,diskraw):
	diskmodel = mycon.run("diskinfo " + diskraw + "| grep 'product id:' | awk -F: '{print $NF}'",'s')
	return diskmodel
	

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

def extract_ivmhostinfo(host):
	guests = mycon.run("/opt/hpvm/bin/hpvmstatus -M | awk -F : '{print$1}'")
	for guest in guests:
		guest = guest.rstrip('\n')
		hpivmhosts[host][guest]=[]
		#Get all disks for given guest
		comando = "/opt/hpvm/bin/hpvmdevinfo -M -P " + guest + " | grep -v 'lv' | awk -F : '/disk/{print $2,$8,$9}'"
		disks = mycon.run(comando)
		for linedisk in disks:
			linedisk = linedisk.split(' ')
			diskhost = linedisk[1].rstrip('\n')
			comando = "ls -la " + diskhost + " >/dev/null 2>&1; echo $?"
			existe =  mycon.run(comando,'s')
			if int(existe) == 0:
				diskguest = linedisk[2].rstrip('\n')
				diskwwid = extract_wwid(diskhost)
				disksize = extract_disksize(host,diskhost)
				diskmodel = extract_diskmodel(host,diskhost)
				dtmp = {'hdisk':diskhost,'gdisk':diskguest,'size':disksize,'model':diskmodel,'wwid':diskwwid}
				hpivmhosts[host][guest].append(dtmp)
def show_hpivminfo(host):
        table = []
	table_resume = []
	headersivm = ['Host','Guest','Virt disk','Phy Disk','WWID','Size Gb','Model']
	headersivm_resume = ['Host','Guest','Total Size Gb']
	for guest in hpivmhosts[host]:
		sizetotal = 0
		for disk in hpivmhosts[host][guest]:
			line = [host,guest, disk['gdisk'], disk['hdisk'], disk['wwid'], (int(disk['size'])/1024)/1024, disk['model']]
			table.append(line)
			sizetotal = (sizetotal + (int(disk['size'])/1024)/1024)
		line_resume = [host,guest,sizetotal]
		table_resume.append(line_resume)

	if output == 'csv':
		global write_hpimvinfo
                if write_hpimvinfo == 0:
			write_csv(headersivm, exportpath + "hpivminfo.csv")
                        write_csv(headersivm_resume, exportpath + "hpivminfo_resume.csv")
			write_hpimvinfo = 1


		write_csv(table, exportpath + "hpivminfo.csv")
		write_csv(table_resume, exportpath + "hpivminfo_resume.csv")

		

	else:
		print tabulate(table,headersivm,tablefmt="psql")
		print tabulate(table_resume,headersivm_resume,tablefmt="psql")
		
def write_csv(dataexport,outfile):
                with open(outfile, "wb") as f:
	                writer = csv.writer(f,delimiter=';')
                        writer.writerows(dataexport)


# ----------------------- MAIN ------------------------------
hpivmhosts={}
vgsdatadict={}
write_vginfo_header = 0

#TODO implement getopts for more robust parameters input
if len(sys.argv)== 2 and sys.argv[1]=='csv':
	output = 'csv'
	if not os.path.exists(exportpath):
    		os.makedirs(exportpath)
else:
	output = 'table'

for host in hosts:
	#All functions that need connect to a server will use the variable 'host' to execute the commands on remote system
	#remove \n for ssh connection
	host=host.rstrip('\n')
	vgsdatadict[host]={}
	vgsdatadict[host]['vgs']={}
	mycon = Con_manager()
	mycon.open_con(host)

	if is_hpivm() == 'host':
		vgsdatadict[host]['hpivm']='host'
		hpivmhosts[host]={}
		extract_ivmhostinfo(host)
		show_hpivminfo(host)
	elif is_hpivm() == 'guest':
		hpivmhost = extract_hpivmhost()
		vgsdatadict[host]['hpivm']='guest'
		vgsdatadict[host]['hpivmhost']=host
	else:
		#Is string False because is not boolean (guest,host or False)
		vgsdatadict[host]['hpivm']='False'

	extract_vgdata(host)

	#Obtener modelo e introducirlo en el dict una vez procesadas las entradas de vgdisplay
	extract_pvmodel()

	mycon.close()
	showvginfo(host)
