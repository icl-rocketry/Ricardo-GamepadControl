import pygame
import socketio
import sys
import json
import copy
import requests
from pylibrnp import defaultpackets
import time


class GamepadControl():
    def __init__(self,config:str,joy_id:int,backend_host:str,backend_port:int,fps:int,sendDelta:int,verbose:bool,debug:bool):

        self.verbose = verbose
        self.debug = debug
        self.configFilepath = config
        self.sendDelta = sendDelta
        self.prevTime = 0
        #setup sio stuff
        self.sio = socketio.Client(logger=False,engineio_logger=False)

        if backend_host is None or backend_port is None:
            self.sio = None
        
        self.backend_url = "http://" + backend_host + ":" + str(backend_port) + '/'

        self.config = {'Axes':{},'Buttons':{}}
        
        if self.processConfig():
            sys.exit(0)
        # print(self.config)

        if joy_id is None:
            #print all joys and exit
            pygame.joystick.init()
            [print(str(x) + " : " + str(pygame.joystick.Joystick(x))) for x in range(pygame.joystick.get_count())]
            sys.exit(0)


        #pygame stuff
        pygame.init()
        self.screensize = (500,500)
        self.screen = pygame.display.set_mode(self.screensize)
        pygame.display.set_caption("Joystick TVC")

        iconImg = pygame.image.load('misc/Images/logo.png')
        image = pygame.transform.scale(iconImg,self.screensize)
        self.screen.blit(image,(0,0))
        pygame.display.flip()
        pygame.joystick.init()
        self.clock = pygame.time.Clock()
        self.joy_id = joy_id
        self.joystick = pygame.joystick.Joystick(joy_id) #this might fail?

        self.fps = fps

        
    def run(self):
        self.sioconnect()
        done = False
        while not done:
            for event in pygame.event.get():

                if self.debug:
                        print(event)

                if event.type == pygame.QUIT:
                    done = True  # Flag that we are done so we exit this loop.
                    break

                if event.type == pygame.JOYDEVICEREMOVED:
                    print("Joystick disconnected quitting")
                    if event.instance_id != self.joy_id: #ignore events not associated with the bound joystick
                        pass
                    done = True
                    break

                if event.type == pygame.JOYBUTTONDOWN:
                    if event.instance_id != self.joy_id: #ignore events not associated with the bound joystick
                        pass
                    #event.button
                    if self.verbose:
                        print("Button:" + str(event.button) + " on")
                    try:
                        button_actions = self.config['Buttons'][str(event.button)]['on']
                        [action.execute() for action in button_actions]
                    except KeyError:
                        pass

                if event.type == pygame.JOYBUTTONUP:
                    if event.instance_id != self.joy_id: #ignore events not associated with the bound joystick
                        pass

                    if self.verbose:
                        print("Button:" + str(event.button) + " off")

                    try:
                        button_actions = self.config['Buttons'][str(event.button)]['off']
                        [action.execute() for action in button_actions]
                    except KeyError:
                        pass

            if (time.time_ns() - self.prevTime > self.sendDelta * 1e6):
                self.prevTime = time.time_ns()
                for axis in range(self.joystick.get_numaxes()):
                    axis_value = self.joystick.get_axis(axis)
                    try:
                        axis_actions = self.config['Axes'].get(str(axis),None)
                        if axis_actions is not None:
                            [action.execute(axis_value) for action in axis_actions]
                    except KeyError:
                            pass

            self.clock.tick(self.fps) #update rate 100ms

        pygame.quit()
              

    def sioconnect(self):
        if self.sio is not None:
            while True:
                try:
                    self.sio.connect(self.backend_url ,namespaces=['/','/packet'])
                    break
                except socketio.exceptions.ConnectionError:
                    print('Server not found, attempting to reconnect!')
                    self.sio.sleep(1)


    def processConfig(self):
        try:
            with open(self.configFilepath, 'r',encoding='utf-8') as file:
                try:
                    config = json.load(file)
            
                    if not config:
                        print('Emtpy Json Config')
                        return True

                    axes = self.config['Axes']
                    #process axis
                    for key,value in config['Axes'].items():
                        #construct trasnform
                        transform = value.get('transform',None)
                        transformFunc = lambda x:x

                        if transform is None:
                            pass
                        elif (transform['type'] == "map"): #check floating point here vs integer division
                            transformFunc = lambda x: (transform['max'] - transform['min'])*(max(min(x,1),-1) - (-1.)) / (1. - (-1.)) + transform['min']
                        
                        actions = []
                        for target in value.get('target'):
                            targetType = target['type']
                            currentAction = None

                            if targetType == "RNP":
                                if (self.sio is not None):
                                    currentAction = SIOTarget(transformFunc,target,self.sio,self.verbose)
                            elif targetType == "POST":
                                currentAction = RESTTarget(transformFunc,target,self.verbose)
                            
                            if currentAction is not None:
                                actions.append(currentAction)

                        axes[key] =  actions
                    
                    buttons = self.config['Buttons']
                    #process buttons
                    for key,value in config['Buttons'].items():                     
                        
                        buttons[key] = {}
                        for state,targetList in value.items():
                            actions = []

                            for target in targetList:
                                targetType = target['type']
                                currentAction = None

                                if targetType == "RNP":
                                    if (self.sio is not None):
                                        currentAction = SIOTarget(None,target,self.sio,self.verbose)
                                elif targetType == "POST":
                                    currentAction = RESTTarget(None,target,self.verbose)
                                
                                if currentAction is not None:
                                    actions.append(currentAction)

                            (buttons[key])[state] = actions
                        
                    
                except json.JSONDecodeError:
                    print('Invalid json file!')
                    return True
                except KeyError as e:
                    print(e)
                    print('Error key invalid!')
                    raise e
                    return True
        except FileNotFoundError:
            print('No Config File')
            return True
        #consturct transform objects
        #construct targets

        
        
class SIOTarget():
    def __init__(self,transform:dict,config:dict,sioInstance,verbose:bool):
        self.transform = transform
        self.sioInstance = sioInstance
        self.config = config
        self.verbose = verbose

        self.cmd_packet : defaultpackets.SimpleCommandPacket = defaultpackets.SimpleCommandPacket(command = int(self.config['command_id']))
        self.cmd_packet.header.destination_service = int(self.config['destination_service'])
        self.cmd_packet.header.source_service = int(self.config['source_service'])
        self.cmd_packet.header.source = int(self.config['source'])
        self.cmd_packet.header.destination = int(self.config['destination'])
        self.cmd_packet.header.packet_type = 0
        

    def execute(self,value:float = None):

        if value is None:
            self.cmd_packet.arg = int(self.config['command_arg'])
        else:
            self.cmd_packet.arg = int(self.transform(value))

        if self.verbose:
            address_string = str(self.cmd_packet.header.source) + ":" +str(self.cmd_packet.header.source_service) + "->" + str(self.cmd_packet.header.destination) + ":" +str(self.cmd_packet.header.destination_service)
            print("SIO Send ["+ address_string + "]:" + str(self.cmd_packet.arg))

        try:
            self.sioInstance.emit('send_data',{'data':self.cmd_packet.serialize().hex()},namespace='/packet')
        except socketio.exceptions.BadNamespaceError:
            pass
        

class RESTTarget(): #only post for now 
    def __init__(self,transform:dict,config:dict,verbose:bool):
        self.transform = transform #if None, then we have all info required
        self.config = config
        self.restPayload = copy.deepcopy(self.config['payload'])
        self.verbose = verbose

    def execute(self,value:float = None):

        if value is not None:
            try:
                self.restPayload[self.config['value_name']] = self.transform(value)
            except KeyError:
                print('error occured when updating field in rest payload!')
                pass
        
        if self.verbose:
            print("REST POST:" + str(self.restPayload))

        r = requests.post(self.config['url'],json=self.restPayload)
        if r.status_code != 200:
            print('Send Error')
            print(r.status_code,r.reason)


        

