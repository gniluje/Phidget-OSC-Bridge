"""
----------------- Phidget1012toOSC_python ---------------
Program enabling a 2 way OSC dialog with a Phidget 1012.
It launches in parallel a small OSC server and a small OSC client
which can enable to link Phidget 1012 with OSC piloted software like madmapper or chataigne.
If no serial number inputed, it will detect the first Phidget1012 attached
The OSC message expected is the following :
- /pidget1012/[channel]/[value] if no serial number inputed
- /[serialnumber]/[channel]/[value] if a serial number was inputed
---------------------------------------------------------
"""

# Common importations
import argparse
from argparse import RawTextHelpFormatter
import asyncio
import traceback
import time
import sys

# Phidget importations
from Phidget22.Phidget import *
from Phidget22.PhidgetException import PhidgetException
from Phidget22.Devices.DigitalInput import DigitalInput
from Phidget22.Devices.DigitalOutput import DigitalOutput

# Python-osc importations
from pythonosc import osc_message_builder, udp_client, dispatcher, osc_server

# Phidget Constants
PHIDGET_SERIAL_NUMBER = 498255  # Replace with your Phidget's serial number
PHIDGET_CHANNEL_NUMBER = 16

# OSC Constants
OSC_SERVER_IP = "127.0.0.1"  # Replace with the OSC server's IP
OSC_SERVER_PORT = 5000  # Replace with the OSC server's port
OSC_CLIENT_IP = "127.0.0.1"  # Replace with the OSC client's IP
OSC_CLIENT_PORT = 5001  # Replace with the OSC client's port

OSCDefaultState = 0
noError = 1

DESCRIPTION = "----------------- Phidget1012toOSC_python ---------------\n\n\
Program enabling a 2 way OSC dialog with a Phidget 1012.\n\
It launches in parallel a small OSC server and a small OSC client\n\
which can enable to link Phidget 1012 with OSC piloted software like madmapper or chataigne.\n\n\n\
If no serial number inputed, it will detect the first Phidget1012 attached\n\n\n\
The OSC message expected is the following :\n\
- /pidget1012/[channel]/[value] if no serial number inputed\n\
- /[serialnumber]/[channel]/[value] if a serial number was inputed\n\n\
---------------------------------------------------------"

print(DESCRIPTION)

parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=RawTextHelpFormatter)

parser.add_argument("-sip", "--serverip", default="127.0.0.1", help="The ip to listen on")
parser.add_argument("-sp","--serverport", type=int, default=5000, help="The port the OSC Server is listening on")
parser.add_argument("-cip","--clientip", default="127.0.0.1", help="The ip of the OSC server")
parser.add_argument("-cp","--clientport", type=int, default=5001, help="The port the OSC Client is listening on")
parser.add_argument("-sn","--serialnumber", type=int, default=None, help="Phidget serial number if wanted")
args = parser.parse_args()

OSC_SERVER_IP = args.serverip # Replace with the OSC server's IP
OSC_SERVER_PORT = args.serverport  # Replace with the OSC server's port
OSC_CLIENT_IP =  args.clientip  # Replace with the OSC client's IP
OSC_CLIENT_PORT = args.clientport  # Replace with the OSC client's port

# Define Phidget serial number and OSC address
PHIDGET_SERIAL_NUMBER = args.serialnumber  # Replace with your Phidget serial number

def exit_program():
    print("Exiting the program...")
    sys.exit(0)

def onAttach(self):
    print("Attach [" + str(self.getChannel()) + "]!")

def onDetach(self):
    print("Detach [" + str(self.getChannel()) + "]!")

def onError(self, code, description):
    errorName = ErrorEventCode.getName(code)
    print("Channel [" + str(self.getChannel()) + "]: " + "Error code = " + errorName)
    print("Description : " + str(description))
    print("----------")

    match errorName:
        case EEPHIDGET_BUSY:
            print("Unable to connect to the Phidget unit")
            print("Check if an other program is using the Phidget you are trying to attach")
            noError = 0

# Define a function to send OSC messages
def send_osc_message(osc_address, state):
    client = udp_client.SimpleUDPClient(OSC_CLIENT_IP, OSC_CLIENT_PORT)
    value = state if state else OSCDefaultState
    print(f"[    =>] Message sent to ip address {OSC_SERVER_IP} through the port {OSC_CLIENT_PORT} = {osc_address} value = {value}")
    client.send_message(osc_address,value)

def onStateChange(self, state):
    print(f"[~~~~~~] Button {self.getChannel()} state change : {state}")
    if PHIDGET_SERIAL_NUMBER:
        osc_address = f"/{self.getDeviceSerialNumber()}/{self.getChannel()}/"
    else :
        osc_address = f"/phidget1012/{self.getChannel()}/"
    osc_address = osc_address.replace(" ", "")
    send_osc_message(osc_address,state)

# Create a Phidget DigitalIutput list
digitalInput = []

# Populate the list
for i in range(PHIDGET_CHANNEL_NUMBER):
    digitalInput.append(DigitalInput())

# Set serial number device
if PHIDGET_SERIAL_NUMBER :
    for i in range(PHIDGET_CHANNEL_NUMBER):
        digitalInput[i].setDeviceSerialNumber(PHIDGET_SERIAL_NUMBER)

# Set Channel and common handlers
for i in range(PHIDGET_CHANNEL_NUMBER):
    digitalInput[i].setChannel(i)
    digitalInput[i].setOnAttachHandler(onAttach)
    digitalInput[i].setOnDetachHandler(onDetach)
    digitalInput[i].setOnErrorHandler(onError)
    digitalInput[i].setOnStateChangeHandler(onStateChange)

# Create a Phidget DigitalOutput list
digitalOutput = []

# Populate the list
for i in range(PHIDGET_CHANNEL_NUMBER):
    digitalOutput.append(DigitalOutput())

# Set serial number device
if PHIDGET_SERIAL_NUMBER :
    for i in range(PHIDGET_CHANNEL_NUMBER):
        digitalOutput[i].setDeviceSerialNumber(PHIDGET_SERIAL_NUMBER)
  
# Set Channel and common handlers
for i in range(PHIDGET_CHANNEL_NUMBER):
    digitalOutput[i].setChannel(i)
    digitalOutput[i].setOnAttachHandler(onAttach)
    digitalOutput[i].setOnDetachHandler(onDetach)
    digitalOutput[i].setOnErrorHandler(onError)

# filter handler of osc message received
def filter_handler(address, channel, *args ):
    ch = channel[0]
    value = args[0]
    print(f"[<=    ] OSC message received on channel {ch} : {address}/{value}")
    if value in [0, 1] :
        print(f"[~~~~~~] Set output channel {ch} to {value}")
        digitalOutput[ch].setState(value)
    else :
        print(f"Error : value = {value} out of range, must be 0 or 1")


# Init dispatcher
dispatcher = osc_server.Dispatcher()

print("-----------------------------------------")
print(f"List of OSC addresses server is listening on (ip {OSC_SERVER_IP}, port {OSC_SERVER_PORT}):")
# Create and map dispatcher handlers from serial number
for i in range(PHIDGET_CHANNEL_NUMBER):
    if PHIDGET_SERIAL_NUMBER :
        filter_dispatcher_address = f"/{PHIDGET_SERIAL_NUMBER}/{i}"
    else :
        filter_dispatcher_address = f"/phidget1012/{i}"
    print(filter_dispatcher_address)
    dispatcher.map(filter_dispatcher_address, filter_handler, i)


# Main async loop
async def loop():
    
    while noError:
            await asyncio.sleep(1)
    
# Main async main function
async def init_main():
    try:
        # wait for input and output attachments
        print("-----------------------------------------")
        print("Attaching Phidget inputs :")
        for i in range(PHIDGET_CHANNEL_NUMBER):
            digitalInput[i].openWaitForAttachment(5000)
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.5)

        print("-----------------------------------------")
        print("Attaching Phidget outputs :")
        for i in range(PHIDGET_CHANNEL_NUMBER):
            digitalOutput[i].openWaitForAttachment(5000)
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.5)
        
        print("-----------------------------------------")
        print("resetting Phidget outputs to 0")
        for i in range(PHIDGET_CHANNEL_NUMBER):
            digitalOutput[i].setDutyCycle(0)
        await asyncio.sleep(0.5)

        server = osc_server.AsyncIOOSCUDPServer((OSC_SERVER_IP, OSC_SERVER_PORT), dispatcher, asyncio.get_event_loop())
        transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

        print("-----------------------------------------")
        print("OSC client and server launched, waiting for incoming OSC signal or input changes")
        print("-----------------------------------------")

        await loop()  # Enter main loop of program

        transport.close()  # Clean up serve endpoint

    except PhidgetException as ex:
        #We will catch Phidget Exceptions here, and print the error information.
        traceback.print_exc()
        print("")
        print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)
        

    finally:   
    # Close the Phidget devices
        #Close your Phidgets once the program is done.
        for i in range(PHIDGET_CHANNEL_NUMBER):
            digitalInput[i].close()
            digitalOutput[i].close()


asyncio.run(init_main())