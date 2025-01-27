# Phidget-OSC-Bridge

Python executable enabling to read the input signals and control the output signals of a phidget 1012 card via the use of the OSC protocol.
Very specific and basic for the moment, more an alpha than a beta version. Tested on Windows.

Based on an asynchronous multithreaded OSC server/client which route phidget events.

Third party python modules are (There is a requirement.txt if needed) : 
python-osc
phidget22

You need to have Phidget22 librairies installed on your PC to develop : https://www.phidgets.com/docs/Operating_System_Support

If you want to create an .exe including a python executable with everything needed and the phidget22.dll, you can install pyinstaller and use the script CreateExe.bat
