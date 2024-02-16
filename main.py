import pygame
import argparse
import gamepadcontrol
import sys

#setup joystick 
#command line arg for which joystick mapping to use (i.e config path), 
#command line arg for which joystick id to use give list of current joysticks if muliple exist on system or specify guid?
# command line arg for update rate 
# load mapping from config folder?? what does mapping even look like
# we have buttons vs axis 





if __name__ == "__main__":
    # Argument Parsing
    ap = argparse.ArgumentParser()

    ap.add_argument("-n", "--joy_n", required=False, help="joystick device to use", type=int,default = None)

    ap.add_argument("-c", "--config", required=False, help="filepath to config file", type=str,default = "config/default.json")

    ap.add_argument("--host", required=False, help="backend host", type=str,default="localhost")
    ap.add_argument("--port", required=False, help="backend Port", type=int,default = 1337)

    args = vars(ap.parse_args())

    gc = gamepadcontrol.GamepadControl(args['config'],args['joy_n'],args['host'],args['port']) 

    gc.run()

    sys.exit(0)