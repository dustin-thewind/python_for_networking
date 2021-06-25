#Created by Dustin Baker
#this runs on the probe system
#this code has been tested to run on Ubuntu 14.04 LTS

import sys
import time
import datetime
import socket
import os
import os.path
import platform
import re
import speedtest
import urllib2
import timeout_decorator
from fabric.operations import *
from timeit import default_timer as timer
'''
REQUIRED PACKAGES:
0) run apt-get install git
1) run apt-get install python-pip
2) sudo pip install speedtest-cli
3) sudo pip install timeout-decorator
4) sudo apt-get install fabric
'''
#*****************************************HOUSEKEEPING**************************

#*****************************************/HOUSEKEEPING*************************


#*****************************************VARS**********************************
#default duration for sleep timers
global sleep_duration
sleep_duration = 4
#list of url's to check to verify internet connectivity
global url_list
url_list = ['www.google.com','www.netflix.com','www.aws.amazon.com/console/']
#directory for log files
global device_ID
device_ID = 'US-CA-SD-B1'
global log_file_dir
log_file_dir= '/home/test/WiPy/Logs/'
#log file name
global log_file_name
log_file_name = device_ID+'-WiPy.txt'
global temp_log_file_name
#*****************************************/VARS*********************************


#************************************FUNCION DEFS*******************************
#get the system time to append to a file name
#@return the file with the timestamped name
def date_time_stamp(fname, fmt='%Y-%m-%d-%H-%M-%S_{fname}'):
    return datetime.datetime.now().strftime(fmt).format(fname=fname)

#checks if specified URL is accessible
#return true if found
#else return false
def url_up(url):
	try:
		urllib2.urlopen('http://'+url)
		return True
	except urllib2.URLError:
		return False

#connects the system to the SSID specified
#@timeout_decorator.timeout(10)
def connect_wifi(ssid):
    print('Attempting to connect to '+ssid)
    os.system('nmcli c up id '+ssid)
    print ('Connected successfully to '+ssid)
    return 1

#calls the connect wifi def and provides some error handling
def call_connect_wifi(wifi_ssid):
	selection = -1
	while selection < 0:
	    try:
		selection = connect_wifi(wifi_ssid)
	    except:
		print('Issues connecting to '+wifi_ssid+' would you like to try reconnecting?')
		print('0) Try again')
		print('1) Cancel test')
		selection = input('choice> ')
		if selection == 0:
		    selection = -1
		else:
		    selection = 1
	return selection

#disables the wifi card in the system
def disable_wifi():
    try:
        os.system('nmcli nm wifi off')
	time.sleep(sleep_duration)
    except:
	print('Issues disabling wifi')

#enables the wifi card in the system
def enable_wifi():
    try:
        os.system('nmcli nm wifi on')
	time.sleep(sleep_duration)
    except:
	print('Issues enabling wifi')

#brings the wifi up and down
def reset_wifi():
    try:
	disable_wifi()
        time.sleep(7)#we wait longer here to allow the AP association to clear
        enable_wifi()
	time.sleep(sleep_duration)
	print('Successfully reset wireless network hardware')
    except:
        print('Issues resetting wireless network hardware')

#checks to see if the specified sites are accessible
#@param url_list - list of sites to check
def inet_access():
    checkCount = 0
    try:
        for url in url_list:
            if url_up(url):
                print('Site ' + url + ' is available')
                checkCount+=1
            if not url_up(url):
		print('Site ' + url + ' is not reachable. Consider checking internet connection.')
		pass
            if checkCount==len(url_list):
		print('All sites were accessible!')
    except:
        exit('Internet is down.')

def execute_system_process(command):
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

#run a speedtest using the pyspeedtest API
def check_speed():
    try:
	print('#'*10+'START SPEEDTEST'+'#'*10)
        for path in execute_system_process('/usr/local/bin/speedtest-cli'):
            print(path)
	print('#'*11+'END SPEEDTEST'+'#'*11)
    except:
        print('Issues running speedtest')

#calls all the defs needed to test an invidivual SSID
def connect_and_test(ssid):
    start_time = timer()
    reset_wifi()
    time.sleep(sleep_duration)
    call_connect_wifi(ssid)
    time.sleep(sleep_duration)
    check_speed()
    inet_access()
    end_time = timer()
    print('Time Elapsed: {:.2f} seconds'.format(end_time-start_time))
    print('Moving on to next SSID to test, if there is one.')
    print('Please be patient.....')
    print('*')*30

#close the log file
def close_log_file():
	logging_file.close()

#opens the log file
def open_log_file():
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
    temp_file_name = os.path.join(log_file_dir,date_time_stamp(log_file_name))
    return temp_file_name
    #write everything we print out to the log file

#uses the SCP functionality of the fabric module to copy the file
def copy_file():
    env.user = 'dbaker1' #need to remove this hard code and abstract
    env.password = user_pass
    put(temp_log_file_name,'/WiPy/Logs')

#handles outputting to sys.stdout and to the log file
class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for logging_file in self.files:
            logging_file.write(obj)

#calls all the functions needed to run a complete test
def run_test():
        print('\n')
        print('#############TEST START MARKER############')
    	print('Test is starting...')
    	print('Resetting network hardware. Please be patient...')
    	enable_wifi() #wifi on the system will be disabled by default
    	connect_and_test('ILLUMINA')
    	connect_and_test('iVisitor')
    	disable_wifi() #disable the wifi after the tests finish
    	print('All tests passed. You did a good job! Now time to have a beer...')
        print('##############TEST END MARKER#############')
        logging_file.close()

#create a log file in the specified directory with a timestamp
temp_log_file_name = open_log_file()
logging_file = open(temp_log_file_name,'wb')
backup = sys.stdout #this prints all output to std.out and logfile
#sys.stdout = backup to revert back to only printing to console
sys.stdout = Tee(sys.stdout, logging_file)
#************************************/FUNCION DEFS******************************

#*****************************************************************************#
#*******************************main******************************************#
if __name__ == '__main__':
    run_test()
