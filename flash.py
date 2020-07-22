import subprocess
import pyudev
import json
from time import sleep
import os
import wifi_connect
import threading
import OPi.GPIO as GPIO

# ASSUMED THAT THIS COMMAND HAS ALREADY BEEN RUN
# sudo mkdir /mnt/usb_stick

#Directory to mount SD
MOUNT_DIR = "/root/UsbStick"

#Method to execute bash commands
def run_command(command):
    try:
        ret_code, output = subprocess.getstatusoutput(command)
        if ret_code == 1:
            raise Exception("FAILED: %s" % command)
        return output.splitlines() 
    except Exception as e:
        print(e)

#Get uuid of device 
def uuid_from_line(line):
    return line[:9]


def getInterfaceName():                                                              # Get name of the Ethernet interface
    try:
        for dirs in os.walk('/sys/class/net'):
            print (dirs)
            for dir in dirs:
                if dir[:3] =='eth' or dir[:4]=='wlan':
                    interface=dir
    except:
        interface="None"
    return interface


def getMAC(interface):                                                               # Return the MAC address of the specified interface                                                    
    try:
        str = open('/sys/class/net/%s/address' %interface).read()
    except:
        str = "00:00:00:00:00:00"
    return str[0:17]


def start(connectionObject):
    try:                                        # Recieve current interface
        GPIO.setwarnings(False)                                                             # Ignore warning for now
        GPIO.setmode(GPIO.BOARD)                                                            # Use physical pin numbering
        GPIO.setup(18, GPIO.OUT, initial=GPIO.HIGH)                                         
        GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)
        macAddrWlan0 = getMAC('wlan0')                  
        macAddrEth0 = getMAC('eth0')
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='usb')

        for device in iter(monitor.poll, None):
            GPIO.output(18, GPIO.HIGH)
            GPIO.output(16, GPIO.LOW)
            if device.action == 'add':
                if str(device) == "Device('/sys/devices/platform/soc/1c1b000.usb/usb3/3-1/3-1:1.0')" :
                    print('{} connected'.format(device))
                    sleep(3)
                    output = run_command("blkid | grep LABEL | grep -v boot")
                    for usb_device in output:
                        if '/dev/sd' in uuid_from_line(usb_device):
                            GPIO.output(18, GPIO.LOW)
                            GPIO.output(16, GPIO.HIGH)
                            print ("mounting")
                            command = "mount %s %s" % (uuid_from_line(usb_device), MOUNT_DIR)
                            run_command(command)
                            usbSettings = open("/root/UsbStick/settings.json", "r")
                            sleep(1)
                            settings = json.load(usbSettings)
                            print (settings)    
                            usbSettings.close() 
                            localSettings = open("/root/new_opi/settings.json", "w")
                            json.dump(settings, localSettings)
                            localSettings.close()
                            if 'WIFI' in settings:
                                if settings['WIFI']!=None:
                                    print("connecting to wifi...")
                                    wifi_connect.connect(settings)
                                else:
                                    print("disconnecting from wifi...")
                                    wifi_connect.disconnect()
                            else:
                                print ('no WIFI key')
                                wifi_connect.disconnect()
                            try:
                                macAddrFile = open("/root/UsbStick/bhMac.txt", "a")
                                macAddrFile.write("WLAN: " + macAddrWlan0 + " Ethernet "+ macAddrEth0 + "\n")
                                macAddrFile.close()
                            except:
                                pass
                            
                            try:
                                command = "umount %s" %MOUNT_DIR
                                run_command(command)
                                print("unmounting successfully")
                            except:
                                print ('Err at unmounting')
                            GPIO.output(18, GPIO.HIGH)
                            GPIO.output(16, GPIO.LOW)
                            break
    except Exception as e:
        print(e)
        print ('Flash error')