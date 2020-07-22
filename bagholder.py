import copy
import struct
import json
import socketio
import time
import threading
    
class bagholder_class:
    def __init__(self, inDataBuffer=list(), currentState={key :[0,0,0] for key in range(0,32)}, nullState={key :[0,0,0] for key in range(0,32)}, sensorState=[None,None], baseColorItem=[255,0,0], errorColorItem=[0,255,0], sensorMode=True, newColorFlag=False, status = False, ip = "", port= "", connErrorBuffer= {key :[150,30,0] for key in range(0,32)}):
        #Incoming data dict
        self.inDataBuffer = inDataBuffer
        #Current state of all leds dict
        self.currentState = currentState
        #All leds are off state dict
        self.nullState = nullState
        #Sensor state buffer: [0] current and [1] previous list
        self.sensorState = sensorState
        #Base led colour list
        self.baseColorItem = baseColorItem
        #Error led colour list
        self.errorColorItem = errorColorItem
        #Sensor mode bool
        self.sensorMode = sensorMode
        #Flag if new colour is received from server bool
        self.newColorFlag = newColorFlag
        #Connection to server flag bool
        self.status = status
        #Server name
        self.ip = ip
        #Server port
        self.port = port
        #Server connection error colours dict
        self.connErrorBuffer = connErrorBuffer
        
    #Processing incoming UART data from sensors
    def sensorProcess(self, sensorID, UART_port):
        try:
            self.sensorState[0] = sensorID
            print (self.status)
            if self.status!= False:
                if (self. sensorState[0] in self.currentState) and (self.currentState[self.sensorState[0]] == [0,0,0] or self.currentState[self.sensorState[0]]==self.errorColorItem):   #Sensor wrong
                    if self.sensorState[1] != None and self.currentState[self.sensorState[1]]!=self.baseColorItem:
                        self.currentState[self.sensorState[1]] = [0,0,0]
                    self.currentState[self.sensorState[0]] = self.errorColorItem
                    listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
                    if self.sensorState[0] != self.sensorState[1]:
                        print ('wrong sensor', self.currentState)
                        self.sensorState[1] = self.sensorState[0]  
                elif (self. sensorState[0] in self.currentState) and (self.currentState[self.sensorState[0]] != [0,0,0] and self.currentState[self.sensorState[0]]!=self.errorColorItem):   #Sensor correct
                    self.currentState = copy.deepcopy(self.nullState)
                    listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
                    print ('correct sensor', self.currentState)
                    self.sensorState[1] = self.sensorState[0]
                print (self.sensorState, 'sensor state')
                return listToSend
        except Exception as e: 
            print(e)

    #Sending received data from server via UART to STM32
    def sendReceivedData(self, received, UART_port):
        try:
            self.inDataBuffer.append(int(received))
            self.currentState = copy.deepcopy(self.nullState)
            self.currentState[self.inDataBuffer[0]]= self.baseColorItem
            listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
            del(self.inDataBuffer[0])
            return listToSend
        except Exception as e: 
            print(e)
    #Toggling leds at connect to server   
    def toggleOnConnect(self, UART_port):
        try:
            listToSend = [self.nullState[i][j] for i in self.nullState for j in range(0,3)]
            print (listToSend)
            return listToSend
        except Exception as e: 
            print(e)


    #Returning mac address of specified interface
    def getMAC(self, interface):                                                               # Return the MAC address of the specified interface                                                    
        try:
            str = open('/sys/class/net/%s/address' %interface).read()
        except:
            str = "00:00:00:00:00:00"
        return str[0:17]

    #Connecting to socket.io server
    #Checking if socket connection is up
    def socketConnect(self, socket, UART_port):                    # Checking if socket connection is up
        while True:
            try:
                time.sleep(1)
                #Checking file with params for new adress
                try:
                    config = open('/root/new_opi/settings.json')   # Checking file with params for new adress
                    serverSettings = json.load(config)
                    config.close()
                except:
                    #Creating sample file if missing of broken
                    print('Settings file missing')
                    setFile = open("/root/new_opi/settings.json", "w")
                    settings = {
                        'HOST': "0.0.0.0",
                        'PORT': "0",     
                    }
                    json.dump(settings, setFile)
                    setFile.close()
                #Checking keys in file
                if 'HOST' in serverSettings and 'PORT' in serverSettings:
                    #HOST PORT keys exist and not empty
                    if serverSettings['HOST'] != "" and serverSettings['PORT'] != "" and serverSettings['PORT']!=None:            
                        try:
                            #If disconnected or received new ip
                            if self.ip != serverSettings['HOST'] or self.status==False or self.port != serverSettings['PORT']:   
                                print (serverSettings['HOST'])
                                print (serverSettings['PORT'])
                                socket.disconnect()
                                time.sleep(1)
                                macAddrWlan0 = self.getMAC('wlan0')
                                macAddrEth0 = self.getMAC('eth0')
                                print("connecting to server")
                                connString = 'http://%s:%s/?q=%s_%s' % (serverSettings['HOST'],serverSettings['PORT'], macAddrWlan0, macAddrEth0)
                                print (connString)
                                #Connect and send query with mac adress
                                socket.connect(connString)     
                            elif self.status == True:
                                pass
                        except:
                            #Connection failed
                            self.status = False
                            listToSend = [self.connErrorBuffer[i][j] for i in self.connErrorBuffer for j in range(0,3)]
                            UART_port.write(listToSend)
                            print ("reconnecting")
                    #No ip or port in file
                    elif serverSettings['HOST'] == "" or serverSettings['PORT'] == "":              
                        print ("No IP")
                        self.status = False
                    #Port key is None
                    elif serverSettings['PORT'] == None:
                        try:
                            if self.ip != serverSettings['HOST'] or self.status==False :   # If disconnected or received new ip
                                print (serverSettings['HOST'])
                                socket.disconnect()
                                macAddrWlan0 = self.getMAC('wlan0')
                                macAddrEth0 = self.getMAC('eth0')
                                print("connecting with PORT = null")
                                connString = 'http://%s:80/?q=%s_%s' % (serverSettings['HOST'], macAddrWlan0, macAddrEth0)
                                print (connString)
                                socket.connect(connString)     # Connect and send query with mac adress
                            elif self.status == True:
                                pass
                        except:
                            self.status = False
                            listToSend = [self.connErrorBuffer[i][j] for i in self.connErrorBuffer for j in range(0,3)]
                            UART_port.write(listToSend)
                            print ("reconnecting")
                    self.ip = serverSettings['HOST']
                    self.port = serverSettings['PORT']
                #Port key does not exist
                elif 'PORT' not in serverSettings: 
                    try:
                        if self.ip != serverSettings['HOST'] or self.status==False :   
                            print (serverSettings['HOST'])
                            socket.disconnect()
                            macAddrWlan0 = self.getMAC('wlan0')
                            macAddrEth0 = self.getMAC('eth0')
                            print("connecting with no PORT key")
                            connString = 'http://%s:80/?q=%s_%s' % (serverSettings['HOST'], macAddrWlan0, macAddrEth0)
                            print (connString)
                            socket.connect(connString)     # Connect and send query with mac adress
                            
                        elif self.status == True:
                            pass
                    except:
                        self.status = False
                        listToSend = [self.connErrorBuffer[i][j] for i in self.connErrorBuffer for j in range(0,3)]
                        UART_port.write(listToSend)
                        print ("reconnecting")
                    self.ip = serverSettings['HOST']
                    self.port = None
            except Exception as e:
                print(e)

    