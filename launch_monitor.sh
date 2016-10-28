#!/bin/sh
# Sleep 10 seconds before starting the app to ensure Raspberry is fully booted and connected to Wifi
sleep 10
# Modify this path to where you have copied the script
cd /home/pi/WL-Monitor-Pi
# Replace the tags with your API key and the two stations you would like to display
sudo python monitor.py -k <API-key> <rbl-1> <rbl-2>
cd

