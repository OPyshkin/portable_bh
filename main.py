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
    try:
        # start = time.time()
        ret_code, output = subprocess.getstatusoutput(command)
        if ret_code == 1:
            raise Exception("FAILED: %s" % command)
        print (output.splitlines() )
        return output.splitlines()
    except Exception as e: 
        print(e)

class data_to_send:
    def __init__(self, toSend):
        self.toSend = toSend

    def send_uart(self, port):
        while True:
            try:
                
                if len(self.toSend)>0 and self.toSend != None:
                    print('queue:', self.toSend)
                    port.write(self.toSend[0])
                    del self.toSend[0]
                time.sleep(0.01)
            except Exception as e: 
                print(e)

def file_verification(bh_object):
    
    #for files in os.listdir("/root/new_opi/"):
    try:
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
    except: 
        baseClrFile = open("/root/new_opi/baseColour.json","w")
        print ("file is broken, creating new")
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
    
    try:
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
    except:
        errClrFile = open("/root/new_opi/errColour.json","w")
        print ("err clr file is broken, creating new")
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
    
    try:
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
    except:
        print ("sens file is broken, creating new")
        sensFile = open("/root/new_opi/sensMode.json", "w")
        sMode = {
            'mode' : True
        }
        bh_object.sensMode = sMode['mode']
        json.dump(sMode, sensFile)
        sensFile.close()
    
    try:
        setFile = open("/root/new_opi/settings.json", "r")
        settings = json.load(setFile)
    except:
        print('Settings file missing')
        setFile = open("/root/new_opi/settings.json", "w")
        settings = {
            'HOST': "0.0.0.0",
            'PORT': "0",
            'WIFI': None
        }
        json.dump(settings, setFile)
        setFile.close()
        #settings = json.load(setFile)

    '''
    if settings["WIFI"]!=None:
        pass
        #print("connecting to wifi...")
        #wifi_connect.connect(settings)
    else:
        print("no wifi")
        pass
        #wifi_connect.disconnect()
    '''

        
def polling(port):
    while True:
        try:
            data1 =[b'\xff',b'\xff']
            slaveData = [None,None]
            laserData = [None,None] 
            #print ("polling")
            data = port.read()
            if len(data) != 0:
                if bh_object.currentState != bh_object.nullState and bh_object.sensorMode ==True:
                    #print ("here")
                    data1[0]=data
                    print (data, "raw0")
                    slaveData = struct.unpack('<B', data1[0])
                    for i in range(0,1):
                        data = port.read()
                        print (data, "raw1")
                        #print(data , i)
                        if len(data) != 0:
                            
                            data1[1]=data
                            laserData = struct.unpack('<B', data1[1])
                            if laserData[0] == 0:
                                listToSend = bh_object.sensorProcess(slaveData[0], port_object)
                                dataUart.toSend.append(listToSend)
                                print (slaveData[0], laserData[0], "triggered laser")
                                #print ()
                            elif laserData[0] ==1:
                                #pass
                                print (slaveData[0], laserData[0], "triggered button")
            time.sleep(0.0001)
        except Exception as e: 
            print(e)

if __name__ == "__main__":
    dataUart = data_to_send(list())
    bh_object = bagholder_class()
    port_object = serial.Serial('/dev/ttyS1',115200, timeout =1, stopbits=1)
    socket_object = socketio.Client(reconnection = False) 
    file_verification(bh_object)
    
    
    @socket_object.on('connect')                                                           
    def on_connect():
        try:
            print('connection established')
            bh_object.status = True
            listToSend = bh_object.toggleOnConnect(port_object)
            dataUart.toSend.append(listToSend)
        except Exception as e: 
            print(e)
    
    @socket_object.on('turn')
    def on_message(data):
        try:
            print (data)
            data-=1
            #print (data['data'])
            if data!=None and data not in bh_object.inDataBuffer:
                bh_object.sensorState[1] = None
                listToSend = bh_object.sendReceivedData(data, port_object)
                dataUart.toSend.append(listToSend)
                
        except Exception as e: 
            print(e)
    
    @socket_object.on('settings:color:set:error')                                                   # Error colour sio listener
    def on_set_err_colour(data):
        print ("received error colour " , data)
        try:
            setCol = open("/root/new_opi/errColour.json","w")                                # Write received to file
            bh_object.errorColorItem[0]= data['r']
            bh_object.errorColorItem[1]= data['g']
            bh_object.errorColorItem[2]= data['b']
            #buffer.newColFlag = True
            json.dump(data, setCol)
            setCol.close()
            listToSend = [bh_object.currentState[i][j] for i in bh_object.currentState for j in range(0,3)]
            dataUart.toSend.append(listToSend)
            print (listToSend)
        except Exception as e: 
            print(e)


    @socket_object.on('settings:color:set:base')                                                    # Base colour sio listener
    def on_set_base_colour(data):
        try:
            print ("received base colour " , data)
            setCol = open("/root/new_opi/baseColour.json","w")                               # Write received to file
            bh_object.baseColorItem[0]= data['r']
            bh_object.baseColorItem[1]= data['g']
            bh_object.baseColorItem[2]= data['b']
            json.dump(data, setCol)
            setCol.close()
            listToSend = [bh_object.currentState[i][j] for i in bh_object.currentState for j in range(0,3)]
            dataUart.toSend.append(listToSend)
            print (listToSend)
        except Exception as e: 
            print(e)
        
    
    @socket_object.on('settings:mdm:set')
    def set_sensor_mode(data):
        try:
            bh_object.sensorMode = data
            sensFile = open("/root/new_opi/sensMode.json", "w")
            dataJson = {"mode": data}
            print ("received sens mode " , dataJson)
            json.dump(dataJson, sensFile)
            sensFile.close()
        except Exception as e: 
            print(e)

    @socket_object.on('disconnect')                   # Disconnecting from socket server
    def on_disconnect():
        try:
            print('disconnected from server')
            bh_object.status = False       # Set disconnect flag
        except Exception as e: 
            print(e)

    

    usbTask = Thread(target = flash.start, args=(bh_object,))       #USB drive service
    connectTask = Thread(target = bh_object.socketConnect, args=(socket_object,port_object,))
    pollTask = Thread(target = polling, args=(port_object,))
    sendTask = Thread(target = dataUart.send_uart, args = (port_object,))
    usbTask.start()
    pollTask.start()
    connectTask.start()
    sendTask.start()
    
    
    


 

   
     