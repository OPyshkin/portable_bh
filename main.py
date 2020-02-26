import datetime
from itertools import filterfalse
import serial
import time
from threading import Thread
import socketio
import copy
import ast
import sys
import os
import argparse
import json
import subprocess
from operator import xor
import OPi.GPIO as GPIO
import struct
from bagholder import bagholder_class
#from bagholder import server_connection
import flash
import wifi_connect
import subprocess
# autorun at sudo nano /etc/profile

def run_command(command):
    # start = time.time()
    ret_code, output = subprocess.getstatusoutput(command)
    if ret_code == 1:
        raise Exception("FAILED: %s" % command)
    print (output.splitlines() )
    return output.splitlines() 


def file_verification(bh_object):
    
    #for files in os.listdir("/root/pony/"):
    if "baseColour.json" in os.listdir("/root/new_opi/"):
        print ("base clr file exists")
        baseClrFile = open("/root/new_opi/baseColour.json","r")
        setBaseClr = json.load(baseClrFile)
        bh_object.baseColorItem[0]= setBaseClr['r']
        bh_object.baseColorItem[1]= setBaseClr['g']
        bh_object.baseColorItem[2]= setBaseClr['b']
        baseClrFile.close()
    else:
        baseClrFile = open("/root/new_opi/baseColour.json","w")
        print ("file does not exist, creating file")
        setBaseClr = {
        'r': 0,
        'g': 236,
        'b': 255,
        'hue': 183.5656921585568
        }
        bh_object.baseColorItem[0]= setBaseClr['r']
        bh_object.baseColorItem[1]= setBaseClr['g']
        bh_object.baseColorItem[2]= setBaseClr['b'] 
        json.dump(setBaseClr, baseClrFile)
        baseClrFile.close()

    if "errColour.json" in os.listdir("/root/new_opi/"):
        print ("err clr file exists")
        errClrFile = open("/root/new_opi/errColour.json","r")
        setErrClr = json.load(errClrFile)
        bh_object.errorColorItem[0]= setErrClr['r']
        bh_object.errorColorItem[1]= setErrClr['g']
        bh_object.errorColorItem[2]= setErrClr['b']
        errClrFile.close()
    else:
        errClrFile = open("/root/new_opi/errColour.json","w")
        print ("err clr file does not exist, creating file")
        setErrClr =  {
        'r': 0,
        'g': 236,
        'b': 255,
        'hue': 183.5656921585568
        }
        bh_object.errorColorItem[0]= setErrClr['r']
        bh_object.errorColorItem[1]= setErrClr['g']
        bh_object.errorColorItem[2]= setErrClr['b']
        json.dump(setErrClr, errClrFile)
        errClrFile.close()

    if "sensMode.json" in os.listdir("/root/new_opi/"):
        print ("sens file exists")
        sensFile = open("/root/new_opi/sensMode.json", "r")
        sMode = json.load(sensFile)
        bh_object.sensMode = sMode['mode']
        sensFile.close()
    else: 
        print ("sens file does not exist, creating file")
        sensFile = open("/root/new_opi/sensMode.json", "w")
        sMode = {
            'mode' : True
        }
        bh_object.sensMode = sMode['mode']
        json.dump(sMode, sensFile)
        sensFile.close()

    setFile = open("/root/new_opi/settings.json", "r")
    settings = json.load(setFile)
    
    if settings["WIFI"]!=None:
        print("connecting to wifi...")
        wifi_connect.connect(settings)
    else:
        print("no wifi")
        wifi_connect.disconnect()
    

        
def polling(port):
    try:
        data1 =b'\xff' 
        while True:
            #print ("polling")
            data = port.read()
            if len(data) != 0:
                if bh_object.currentState != bh_object.nullState and bh_object.sensorMode ==True:
                    data1=data
                    slaveData = struct.unpack('<B', data1)
                    print (slaveData[0])
                    bh_object.sensorProcess(slaveData[0], port_object)
            #time.sleep(0.0001)
    except:
        pass

if __name__ == "__main__":
    

    bh_object = bagholder_class()
    port_object = serial.Serial('/dev/ttyS1',115200, timeout =1, stopbits=1)
    socket_object = socketio.Client() 
    file_verification(bh_object)
    #socket_object.connect('http://194.58.109.227:3000/')
    
    #conn_object = server_connection()
    
    @socket_object.on('connect')                                                           
    def on_connect():
        print('connection established')
        bh_object.status = True
        bh_object.toggleOnConnect(port_object)
    
    @socket_object.on('message')
    def on_message(data):
        print (data['data'])
        if data['data']!=None and data['data'] not in bh_object.inDataBuffer:
            bh_object.sensorState[1] = None
            bh_object.sendReceivedData(data['data'], port_object)


    

    @socket_object.on('settings:color:set:error')                                                   # Error colour sio listener
    def on_set_err_colour(data):
        print ("received error colour " , data)
        try:
            setCol = open("/root/new_opi/errColour.json","w")                                # Write received to file
            setCols.errColItem[0]= data['r']
            setCols.errColItem[1]= data['g']
            setCols.errColItem[2]= data['b']
            buffer.newColFlag = True
            json.dump(data, setCol)
            setCol.close()
        except:
            pass


    @socket_object.on('settings:color:set:base')                                                    # Base colour sio listener
    def on_set_base_colour(data):
        print ("received base colour " , data)
        try:
            setCol = open("/root/new_opi/baseColour.json","w")                               # Write received to file
            setCols.baseColItem[0]= data['r']
            setCols.baseColItem[1]= data['g']
            setCols.baseColItem[2]= data['b']
            buffer.newColFlag = True
            #print ("received base colour " , data)
            json.dump(data, setCol)
            setCol.close()
        except:
            pass

    
    @socket_object.on('settings:mdm:set')
    def set_sensor_mode(data):
        try:
            
            sensorOnOff.mode = data
            sensFile = open("/root/new_opi/sensMode.json", "w")
            dataJson = {"mode": data}
            print ("received sens mode " , dataJson)
            
            json.dump(dataJson, sensFile)
            sensFile.close()
        except:
            pass

    @socket_object.on('disconnect')                   # Disconnecting from socket server
    def on_disconnect():
        try:
            print('disconnected from server')
            bh_object.status = False       # Set disconnect flag
            
        except:
            pass

    

    usbTask = Thread(target = flash.start, args=(bh_object,))       #USB drive service
    connectTask = Thread(target = bh_object.socketConnect, args=(socket_object,port_object,))
    pollTask = Thread(target = polling, args=(port_object,))

    usbTask.start()
    pollTask.start()
    connectTask.start()
    
    
    
    


 

   
     
