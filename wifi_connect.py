import subprocess 
import json
import multiprocessing
import time
import main
def run_command(command):
    # start = time.time()
    ret_code, output = subprocess.getstatusoutput(command)
    if ret_code == 1:
        raise Exception("FAILED: %s" % command)
    print (output.splitlines())
    return output.splitlines()

def disconnect():
    #command = "sudo nmcli device disconnect wlan0"
    #res = run_command(command)
    
    command = "LANG=C nmcli d"
    res = run_command(command)
    if 'wlan0   wifi      disconnected  --         ' not in res:
        command = "sudo nmcli device disconnect wlan0"
        res = run_command(command)
        time.sleep(5)
        '''
        command = 'sudo nmcli con down id MyWifi'
        run_command(command)    
        time.sleep(1)
        command = "LANG=C nmcli d"
        res = run_command(command)
        '''
    
        

def connect(settings):
    if settings['WIFI'] == None:
        print ("No wifi")
        
    else:
        disconnect()
       # time.sleep(1)
        print (settings['WIFI'])
        comm = 'sudo nmcli device wifi connect "{}" password {} name "MyWifi"'.format(settings['WIFI']['SSID'], settings['WIFI']['PASSWORD'])
        run_command(comm)
        

            

# In /etc/dhcp/dhclient.conf change timeout.

#subprocess.call("/home/opyshkin/wifi.sh")
