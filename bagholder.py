import copy
import struct
import json
import socketio
import time
import threading

class bagholder_class:
    def __init__(self, inDataBuffer=list(), currentState={key :[0,0,0] for key in range(0,32)}, nullState={key :[0,0,0] for key in range(0,32)}, sensorState=[None,None], baseColorItem=[255,0,0], errorColorItem=[0,255,0], sensorMode=True, newColorFlag=False, ):
        self.inDataBuffer = inDataBuffer
        self.currentState = currentState
        self.nullState = nullState
        self.sensorState = sensorState
        self.baseColorItem = baseColorItem
        self.errorColorItem = errorColorItem
        self.sensorMode = sensorMode
        self.newColorFlag = newColorFlag
        

    def sensorProcess(self, sensorID, UART_port):
        self.sensorState[0] = sensorID
        if (self. sensorState[0] in self.currentState) and (self.currentState[self.sensorState[0]] == [0,0,0] or self.currentState[self.sensorState[0]]==self.errorColorItem):   #Sensor wrong
            if self.sensorState[1] != None and self.currentState[self.sensorState[1]]!=self.baseColorItem:
                self.currentState[self.sensorState[1]] = [0,0,0]
            self.currentState[self.sensorState[0]] = self.errorColorItem
            listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
            if self.sensorState[0] != self.sensorState[1]:
                print ('wrong sensor', self.currentState)
                UART_port.write(listToSend)
                self.sensorState[1] = self.sensorState[0]
        elif (self. sensorState[0] in self.currentState) and (self.currentState[self.sensorState[0]] != [0,0,0] and self.currentState[self.sensorState[0]]!=self.errorColorItem):   #Sensor correct
            self.currentState = copy.deepcopy(self.nullState)
            listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
            print ('correct sensor', self.currentState)
            UART_port.write(listToSend)
            self.sensorState[1] = self.sensorState[0]
        print (self.sensorState, 'sensor state')
        time.sleep(0.010)

    def sendReceivedData(self, received, UART_port):
        self.inDataBuffer.append(int(received))
        self.currentState = copy.deepcopy(self.nullState)
        self.currentState[self.inDataBuffer[0]]= self.baseColorItem
        listToSend = [self.currentState[i][j] for i in self.currentState for j in range(0,3)]
        print (listToSend)
        UART_port.write(listToSend)
        del(self.inDataBuffer[0])
    
    def toggleOnConnect(self, UART_port):
        listToSend = [self.nullState[i][j] for i in self.nullState for j in range(0,3)]
        print (listToSend)
        UART_port.write(listToSend)

class server_connection():
    def __init__(self, status = False, ip = "", port= "", connErrorBuffer= {key :[30,150,0] for key in range(0,32)}):
        self.status = status
        self.ip = ip
        self.port = port
        self.connErrorBuffer = connErrorBuffer

        #bagholder_class.sendReceivedData(self,self.received, self.UART_port)
    def getMAC(self, interface):                                                               # Return the MAC address of the specified interface                                                    
        try:
            str = open('/sys/class/net/%s/address' %interface).read()
        except:
            str = "00:00:00:00:00:00"
        return str[0:17]

    def socketConnect(self, socket, UART_port):                    # Checking if socket connection is up
        while True:
            #print ('socket connect')
            try:
                time.sleep(1)
                config = open('/root/new_opi/settings.json')   # Checking file with params for new adress
                serverSettings = json.load(config)
                config.close()
                if serverSettings['HOST'] != "" and serverSettings['PORT'] != "":            
                    try:
                        if self.ip != serverSettings['HOST'] or self.status==False or self.port != serverSettings['PORT']:   # If disconnected or received new ip
                            print (serverSettings['HOST'])
                            print (serverSettings['PORT'])
                            socket.disconnect()
                            #time.sleep(5)
                            macAddrWlan0 = self.getMAC('wlan0')
                            macAddrEth0 = self.getMAC('eth0')
                            print("connecting here1")
                            socket.connect('http://%s:%s/?q=%s_%s' % (serverSettings['HOST'],serverSettings['PORT'], macAddrWlan0, macAddrEth0))     # Connect and send query with mac adress
                            print("connecting here2")
                        elif self.status == True:
                            
                            pass
                    except:
                        self.status = False
                        listToSend = [self.connErrorBuffer[i][j] for i in self.connErrorBuffer for j in range(0,3)]
                        UART_port.write(listToSend)
                        print ("reconnecting")
                    
                elif serverSettings['HOST'] == "" or serverSettings['PORT'] == "":              # No ip in file
                    print ("No IP")
                    self.status = False
                self.ip = serverSettings['HOST']
                self.port = serverSettings['PORT']
            except Exception as e:
                print(e)

    
    
    