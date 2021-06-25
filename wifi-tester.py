#Wifi Testing Tool
#Created by Dustin Baker
#this script has been tested to run on CentOS 6
#*****************************************************************************#
#*******************************NOTES*****************************************#
'''
REQUIRED PACKAGES:
(comamnds are for CentOS 6)
0) 'yum install git'
1) 'yum install python-pip'
2) 'yum install fabric'
3) 'pip install timeout-decorator'
#4) sudo pip install pyspeedtest (https://github.com/fopina/pyspeedtest)

STUFF TO TEST:
1) limit apache on laptop to accept requests only via WIFI (hard with ivisitor)
2) write all information to a log
3) return time take for tests from laptop - DONE, not optimized
4) set time limit on tests, allow user to cancel if it is taking too long

NOTES:
--due to a bug in ubuntu with PEAP/MSCHAPV2 wireless auth we have to
modify the SSID profile on the target system at /etc/NetworkManager/system-connections
to include the password=PASSWORDHERE for the authenticated user
--In order to ensure wired connectivity stays persistent during wireless connects & disconnects
we have to modify the Wired Connection profile at /etc/NetworkManager/system-connections
to include routes to the system making the calls:
    route#=SYSTEM.IP.HERE/SUBNET,GATEWAY,METRIC-WEIGHT
    (example)route1=192.168.0.10/24,192.168.0.1,0
    we also add never-default=true
--Set the IP of the Wired Connection statically by modifying /etc/network/interfaces
and do no use 'auto IFACE##'
--We modify the /etc/NetworkManager/NetworkManager.conf to change
manged=false to manged=true under [ifupdown]
--We create a keypair between the server and host systems to allow
commands to be executed with needing to re-prompt for password
    -on server: ssh -t keygen, enter through all default operations
    -on server: ssh-copy-id user-to-auth-as@IP.TO.AUTH.TO
    -for example, say you wanted to not be prompted for a login 'test'
    for server 10.10.10.10 you would do ssh-copy-id test@10.10.10.10,
    enter the password when prompted and accept the ssh cert and you should
    be good to go!

BUGS:
-

FUTURE CHANGES:
-would be cool to have a web front end for this
-possibly Django
'''
#import all the packages needed
import sys
import time
import datetime
import socket
import copy
import os
import os.path
import platform
import re
import getpass
#import timeout_decorator
#import paramiko #ssh library
#import pyspeedtest
import urllib2
#the fabric framework for making SSH calls to remote systems
from fabric.api import *
from fabric.tasks import *
from fabric.context_managers import *
from fabric.operations import *
#*****************************************************************************#
#*******************************vars******************************************#
#set the directory to to load the XML from
global xml_file
xml_file = '/WiPy/wifi-tester.xml'
#directory for log files
global log_file_dir
log_file_dir= '/WiPy/Logs/'
global log_file_name
log_file_name = 'WiPy.txt'
#used by wipy_python to set the directory for CD
global remote_app_path
remote_app_path = '/home/test/WiPy/'
#command to run the remote python script
global remote_python_command
remote_python_command = 'python net-access-tester-V2.py'
#the remote directory of the log files
global remote_logfile_dir
remote_logfile_dir = '/home/test/WiPy/Logs/'
#list of all razberry PI IP's
global raz_IP_list
raz_IP_list = []
#*****************************************************************************#
#******************************house keeping**********************************#
#check the XML file to make sure it exists
if os.path.isfile(xml_file):
    print('Hosts file exists and is readable. Proceeding...')
else:
    print("Hosts file doesn't exist! Please check the directory for a valid XML")
xml_file.lstrip()
xml_file.rstrip()
import xml.etree.cElementTree as ET #cElementTree is faster over ElementTree
tree = ET.parse(xml_file)
root = tree.getroot()
if not os.path.exists(log_file_dir):
    os.makedirs(log_file_dir)
#*****************************************************************************#
#*******************************the menus*************************************#
def main_menu():
    print 'TESTAFI WIFI TESTER'
    print 'Pick a site below to test'
    print('            __   __')
    print('           __ \ / __')
    print('          /  \ | /  \\')
    print('              \|/')
    print('         _,.---v---._')
    print('/\__/\  /    DIEGO   \\')
    print('\_  _/ /The Fail Whale\\')
    print('  \ \_|           @ __|')
    print('   \  \_            \\')
    print('    \     ,__/       /')
    print('  ~~~`~~~~~~~~~~~~~~/~~~~')
    print '*************************'

def us_sd_hq_menu_option():
    print('1) Site- SITE')

def us_sd_2_menu_option():
    print('2) Site- SITE')

def exit_main_menu_option():
    print('0) Exit program')

def us_sd_hq_submenu():
    print('SAN DIEGO')
    print('***************')
    print('1) Building 1')
    print('2) Building 2')
    print('3) Building 3')
    print('4) Building 4')
    print('5) Building 5')
    print('6) Building 6')
    print('9) All Buildings')
    print('0) Return to previous menu')

def us_sd_2_submenu():
    print('SAN DIEGO 2')
    print('***************')
    print('1) Building 1')
    print('2) Building 2')
    print('3) Building 3')
    print('9) All Buildings')
    print('0) Return to previous menu')

def run_menu():
    selection = -1
    while selection < 0:
        main_menu()
        us_sd_hq_menu_option()
        us_sd_2_menu_option()
        exit_main_menu_option()
        selection = input('choice> ')
        if selection == 0:
            break
        if selection == 1:
            inner_select = -1
            while inner_select < 0:
                us_sd_hq_submenu()
                inner_select = input('choice> ')
                if inner_select == 0:#exit sub menu condition
                    inner_select = 99 #break the inner_select while loop
                    selection = -1 #return us to the main menu
                    continue
                if inner_select == 1:
                        inner_select = execute_menu_selection('US SD HQ','Building 1')
                if inner_select == 2:
                        inner_select = execute_menu_selection('US SD HQ','Building 2')
                if inner_select == 9:
                        inner_select = execute_menu_selection('US SD HQ','Building 1')
                        inner_select = execute_menu_selection('US SD HQ','Building 2')
                        inner_select = execute_menu_selection('US SD HQ','Building 3')
                        inner_select = execute_menu_selection('US SD HQ','Building 4')
                        inner_select = execute_menu_selection('US SD HQ','Building 5')
                        inner_select = execute_menu_selection('US SD HQ','Building 6')
        if selection == 2:
            inner_select = -1
            while inner_select < 0:
                us_sd_2_submenu()
                inner_select = input('choice> ')
                if inner_select == 0:
                    inner_select = 99 #break the inner_select while loop
                    selection = -1 #return us to the main menu
                    continue
    print('You can view the logs at /WiPy/Logs/')
    print('Thanks for stopping by, San Diego')
#*****************************************************************************#
#*******************************function defintions***************************#
#creates the logfile directory and file name
def create_log_file_name():
    temp_logfile  = os.path.join(remote_logfile_dir,date_time_stamp(log_file_name))
    return temp_logfile

#date/time stamp for the log file
#get the system time to append to a file name
#@return the file with the timestamped name
def date_time_stamp(fname, fmt='%Y-%m-%d-%H-%M-%S_{fname}'):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

#call wipy_python and run it against all the hosts in the list
@task
def execute_wipy_python(raz_IP_list):
    execute(wipy_python, hosts=raz_IP_list)

#run the python script on the remote machine
#cd to the
def wipy_python():
    env.user = user_name
    env.password = user_pass
    #env.sudo_user = user_name
    #with settings(sudo_user):
    with cd(remote_app_path):
        #sudo('cd '+remote_app_path)
        sudo(remote_python_command)

#syncs the log files from the remote system
#using rsync
def log_file_sync():
    print('Syncing logfile data. Please be patient...')
    for ip in raz_IP_list:
        try:
            the_connection_string = 'rsync -a '+user_name+'@'+ip+':'+remote_logfile_dir+' '+log_file_dir
            os.system(the_connection_string)
        except:
            print('We had issues syncing the logs from device with IP '+ip)
    del raz_IP_list[:]#clear the list

#calls create_log_file_name and places log file on remote logging dir
def place_log_file():
    env.user = user_name
    env.password = user_pass
    temp_remote_logfile_name = create_log_file_name()
    print temp_remote_logfile_name
    sudo('touch ' + log_file_name)

#checks if host is upcd
def ping_check(host_name):
    #ping parameters as function of OS
    #supports Windows and UNIX OS
    ping_string = '-n 3' if  platform.system().lower()=='windows' else '-c 3'
    #ping
    return os.system('ping '  + ping_string + ' ' + hostName) == 0

#checks URL to make sure it is reachable
def url_up(url):
	try:
		urllib2.urlopen('http://'+url)
		return True
	except urllib2.URLError:
		return False

#prompt user for creds and store for the duration of execution in memory
def get_creds():
    global user_name, user_pass
    user_name = raw_input(' Enter Username: ')
    user_pass = getpass.getpass(' Enter Password: ')

#execeute the specified menu selction with given params
def execute_menu_selection(site_ID,building_ID):
    try:
        get_creds()
        build_IP_list(site_ID,building_ID)
        execute_wipy_python(raz_IP_list)
        inner_select = -1
        log_file_sync()
    except:
        print('There was an issue executing the selection, returning to menu')
        inner_select = -1
    return inner_select

#build a list raspberry PI IP's given the building name and ID
def build_IP_list(site_name,building_id):
    sites = root.getchildren()#get all sites
    site_list = []
    for site in sites: #iterate through all sites
        site_ID = site.get('name')#get the name of the site
        site_list.append(site_ID)
    #check to make sure we find a match to the site name somewhere in the list
    indices = [i for i, x in enumerate(site_list) if x == site_name]#all indices that match
    if len(indices) == 0:# if we dont find a match the list length will be 0
        print('no match found')
    else:
        for site in sites:
            site_ID = site.get('name')#get the name of the site
            if site_name == site_ID:#match the name of the site_name
                site_children = site.getchildren()#get buildings
                for site_child in site_children:
                    building_identifier = site_child.get('ID')
                    if building_identifier == building_id:#if our build ID matches whats given
                        for sub_child in site_child:#get all sub-children of the building ID
                            if sub_child.tag=='rbpi':#check the tag
                                raz_IP = sub_child.text#get the IP if tag matches
                                raz_IP_list.append(raz_IP)#append the IP to the list of IP's
                            else:
                                pass

#*****************************************************************************#
#*******************************main******************************************#
if __name__ == '__main__':
    run_menu()
