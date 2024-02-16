import pygame
import socketio
import sys
import json

class GamepadControl():
    def __init__(self,config:str,joy_id:int,backend_host:str,backend_port:int,fps:int):

        self.configFilepath = config

        self.config = {}
        
        if self.processConfig():
            sys.exit(0)
        

        if joy_id is None:
            #print all joys and exit
            pygame.joystick.init()
            [print(str(x) + " : " + pygame.joystick.Joystick(x)) for x in range(pygame.joystick.get_count())]
            sys.exit(0)


        #pygame stuff
        pygame.init()
        self.screen = pygame.display.set_mode((500, 500))
        pygame.display.set_caption("Joystick TVC")
        pygame.joystick.init()
        self.clock = pygame.time.Clock()

        self.joy_id = joy_id
        self.joystick = pygame.joystick.Joystick(joy_id) #this might fail?

        self.sio = socketio.Client(logger=False,engineio_logger=False)

        if backend_host is None or backend_port is None:
            self.sio = None
        
        self.backend_url = "http://" + backend_host + ":" + str(backend_port) + '/'

        self.fps = fps

        
    def run(self):
        self.sioconnect()
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True  # Flag that we are done so we exit this loop.

                if event.instance_id is not self.joy_id: #ignore events not associated with the bound joystick
                    pass

                if event.type == pygame.JOYBUTTONDOWN:
                    # print("Joystick button pressed.")
                    #event.button
                    try:
                        button_action = self.config['Buttons'][str(event.button)]['on']
                    except KeyError:
                        pass

                if event.type == pygame.JOYBUTTONUP:
                    # print("Joystick button released.")
                    try:
                        button_action = self.config['Buttons'][str(event.button)]['off']
                    except KeyError:
                        pass

                if event.type == pygame.JOYAXISMOTION:
                    #event.instance_id
                    #event.axis
                    #event.value
                    #retrieve axis from config
                    try:    
                        axis_action = self.config['Axes'][str(event.axis)] #keys are strings

                    except KeyError:
                        pass

                if event.type == pygame.JOYDEVICEREMOVED:
                    print("Joystick disconnected quitting")
                    done = True

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
                except json.JSONDecodeError:
                    print('Invalid json file!')
                    return True
        except FileNotFoundError:
            print('No Config File')
            return True
        #consturct transform objects
        #construct targets

        
        
