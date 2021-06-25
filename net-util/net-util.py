#network utilities tool
import sys
import time
import socket
import os
import os.path
import platform
import re
import pexpect
import paramiko
import getpass

'''
#implement this menu
def displayMenu():
    print('***********************************************************************\n')
    print('*                  NETWORK UTILITES TOOL                              *\n')
    print('***********************************************************************\n')
    print('* WARNING:  IF YOU ARE NOT AUTHORIZED TO ACCESS THIS SYSTEM OR IF YOU *\n')
    print('* INTEND  TO  USE THIS SYSTEM BEYOND THE SCOPE OF YOUR AUTHORIZATION, *\n')
    print('* DISCONNECT IMMEDIATELY.                                             *\n')
    print('*  -----------------------------------------------------------------  *\n')
    print('*                       MAKE YOUR SELECTION BELOW                     *\n')
    print('*  -----------------------------------------------------------------  *\n')
    print('*         1 - shutPorts - shuts/no shuts a range of ports             *\n')
    print('*                         on a range of devices                       *\n')
    print('*                                                                     *\n')
    print('*         2 - manualCommand - run a list of commands against a        *\n')
    print('*							 range of devices                        *\n')
    print('*                                                                     *\n')
    print('*         3 - exit - quit                                             *\n')
    print('*                                                                     *\n')
    print('***********************************************************************\n')
'''

#future features
#-run list of commands against set of devices

#here we should TRY the username and pass to make sure they work
#before prompting the user for the XML file
uName = raw_input('Enter your admin username:')
uPass = getpass.getpass('Enter your password:')
	#try user/pass against device

#this checks to make sure the specified file exists
fileLoc = ''
while not os.path.isfile(fileLoc):
	fileLoc = raw_input('Enter path to XML file:')
	if os.path.isfile(fileLoc):
		print 'File exists and is readable. Proceeding...'
	else:
		print "File doesn't exist! Please re-enter:"

#fileLoc = '/home/dbaker/Desktop/python-test/testfile1.xml'
fileLoc.lstrip()
fileLoc.rstrip()
import xml.etree.cElementTree as ET #cElementTree is faster over ElementTree
tree = ET.parse(fileLoc)
root = tree.getroot()

#checks if host is up
#would like to return successful ping count 
#instead of outputting every ping
def pingCheck(hostName):
    #ping parameters as function of OS
    #supports Windows and UNIX OS
    pingString = "-n 3" if  platform.system().lower()=="windows" else "-c 3"
    #ping
    return os.system("ping " + pingString + " " + hostName) == 0

#this isn't handling the scenario where we don't have SSH token
#need to fix that
#grab ip address and mac of host
	#need a get IP and get MAC method
	#out put those on screen
	#wait for user to respond before proceeding
def shutPorts(hostList):
	child = pexpect.spawn ('ssh '+uName+'@'+hostList[0])
	#build a list of ports
	child.expect('.*assword:.*') #this line is causing issues when we dont have SSH token
	child.sendline(uPass)
	child.expect ('#.*', timeout=10)
	child.sendline('conf t')
	child.expect ('#.*', timeout=10)
	#iterate through all ports in the list
	#skip the first entry in the list since first entry is the switch name
	iterPorts = iter(hostList)
	next(iterPorts)
	for index in iterPorts:
		portNum = index
		child.sendline('interface '+portNum)
		child.expect ('#.*', timeout=20)
		child.sendline('shut')
		child.expect ('#.*', timeout=20)
		print 'interface '+portNum+' is SHUT'
		time.sleep(5)
		child.sendline('no shut')
		child.expect ('#.*', timeout=20)
		print 'interface '+portNum+' is NO SHUT'
	child.sendline('end')
	child.expect ('#.*', timeout=10)
	child.sendline('exit')
	child.close()

#the way we build these XML lists can probably be optimized for memory usage
for switch in root:
		#ports = [port.text for port in switch.findall('port')]
		switchName = switch.get('name')
		switchList = [switchName]
		combinedList = [switchName]
		combinedList += ports
		#print len(combinedList)
		#print len(switchList)
		for host in switchList:
			if 	pingCheck(switchName):
				#print '**********************************'
				print 'Switch ' + host + ' is up!'
				#print '**********************************'
				#print combinedList
				shutPorts(combinedList)
			else:
				#print '**********************************'
				print 'Unable to reach switch ' + host
				print 'Moving on to next device in list'
				#print '**********************************'

#eventually we'll want to loop this with the menu
#until the user selects the option to quit
print 'End of XML, goodbye.'
