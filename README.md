# Overview
Python app allowing gamepads and joysticks to be used to control components in the ricardo avionics ecosystem. Supports both socketIO based packets, as well as sending POST requests to the command server. Probably contains bugs.

# Documentation
High level overview WIP.

# Running
## Local
Install dependencies using the requirements.txt:
```
pip install -r requirements.txt
```

Run:
To list current joysticks avaliable on the system run:
```
python ./main.py 
```
Once the joystick ID is found, use the -n flag to indicate which device to use.
```
python ./main.py -n <joystick_id>
```

Use the -h flag to see all available command line args.

# Testing
WIP
