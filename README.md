# Raspberry Pi Real-Time Public Transport Departure Monitor

Shows a real-time departure countdown for the Vienna public transport network (Wiener Linien).

Minimize the waiting time at bus / tram / subway stops by knowing when to leave your apartment and getting there just in time! The little app runs on the Raspberry Pi and uses the real-time departure service of the Vienna public transport network (Wiener Linien) to show the countdown to the next departures for two different lines at your closest station.

Features:

- Shows the next two departures for two different public transport stops / lines
- Refreshes countdown every 10 seconds (automatically halves refresh rate in case of the first 20 errors)
- Auto-starts when booting your Raspberry Pi
- Configurable through command line parameters
- Configurable color coding for departure time: best time to leave for the public transport stop -> green display. Medium time -> yellow display. Bad time -> red display.
- Errors shown in blue

Data source: Uses [open data](https://www.data.gv.at/katalog/dataset/add66f20-d033-4eee-b9a0-47019828e698) from the City of Vienna.

Code is based on [WL-Monitor-Pi](https://github.com/mabe-at/WL-Monitor-Pi) from Matthias Bendel / [mabe-at](https://mabe.at) and released under the same MIT license - thanks for creating the original project and inspiring this adaption!


## Photos

Departure monitor in action, showing real-time coutdown for two different directions of a bus line in Vienna:

![](https://raw.githubusercontent.com/andijakl/raspberry-pi-public-transport/master/photos/Raspi-Departures.jpg)

Errors with the connection or the service are shown in red:

![](https://raw.githubusercontent.com/andijakl/raspberry-pi-public-transport/master/photos/Raspi-Error.jpg)

The Adafruit LCD display needs to be assembled manually:

![](https://raw.githubusercontent.com/andijakl/raspberry-pi-public-transport/master/photos/Adafruit-Assembly.jpg)


## Preparation

The project requires:

- Raspberry Pi 1-3 plus SD card
- If you have a Raspberry Pi 1 or 2, you need an additional Wireless LAN dongle, e.g., the official Raspberry Pi Wifi dongle ([Amazon](http://amzn.to/2eC3dEP))
- Adafruit RGB LCD and Keypad Kit for Raspberry Pi ([Amazon](http://amzn.to/2eC1jnD))

Request [your free API key](https://www.wien.gv.at/formularserver2/user/formular.aspx?pid=3b49a23de1ff43efbc45ae85faee31db&pn=B0718725a79fb40f4bb4b7e0d2d49f1d1) for using the real time departure services of Wiener Linien. Setup your Raspberry Pi for running Python scripts.


## Running the app

The app shows departures for two stations & directions - these are called RBLs. You can retrieve the IDs from: https://till.mabe.at/rbl/

Start the script on your Raspberry Pi:

```
$ python monitor.py -k <API-key> [-p <primary-rbl>] <rbl-1> <rbl-2>
```

If valid real time data can be retrieved, the real-time countdown is shown in green. It is recommended to supply two RBL IDs; each RBL will get one line in the two-line LCD panel. However, the script also works if only one RBL ID is supplied.

By default, the script shows the next two departure countdowns for each RBL. In case there is currently no available countdown for the line, the script will show 'N/A'.

The (optional) primary RBL has to be one of the two RBLs you supplied. The departure times of this RBL will be analyzed for the display color coding of the departure times. The script looks at the next three departures to see if one of those is in the ideal time window to leave your house.

The best / medium minutes to leave the house can currently only be configured directly in the script (lines 15 / 17). Simply supply the countdown minutes for the best departure (= green display) and medium departure (= yellow display). All other departure times will be shown in red color. Default: countdown values of 3 and 4 are best (green). 2 and 5 are medium (yellow). All other countdown values cause the display to be shown in red.

If there was an error retrieving data from the web service, the display will turn blue to inform you the visible data is a bit older. After the second failed attempt in a row, the display shows the exception message on the display so that you know if it is a network or service issue.

The refresh rate can be configured in the script or as optional parameter (-t <seconds>). By default it is set to 10 seconds. For the first twenty consecutive errors, the retry time is halved (= 5 seconds) to resolve the issue more quickly in case of a temporary network or service issue.

To issue a refresh immediately, press the DOWN button on the LCD pad for one second. The screen will briefly turn yellow to let you know the command was registered.


## Exiting the app

Exit the running app by pressing and holding the SELECT button (left most) on the keypad of the Adafruit LCD board for one second. The display will be turned off and the script exits.


## Autostart the app

Instructions are based on: http://www.instructables.com/id/Raspberry-Pi-Launch-Python-script-on-startup/

```
$ cd /home/pi/WL-Monitor-Pi
$ nano launch_monitor.sh

#!/bin/sh
sleep 10
cd /home/pi/WL-Monitor-Pi
sudo python monitor.py -k <API-key> -p <primary-rbl> <rbl-1> <rbl-2>
cd

$ chmod 755 launch_monitor.sh
$ cd
$ mkdir logs
$ sudo crontab -e

(add line at end)
@reboot sh /home/pi/WL-Monitor-Pi/launch_monitor.sh >/home/pi/logs/cronlog 2>&1
(Ctrl-X, Y, Enter)

$ sudo reboot now
```

## Edit Python script from Windows

An easy way to edit and develop the script is to use a Samba fileshare. 

Full setup instructions: https://blogs.msdn.microsoft.com/mustafakasap/2016/02/04/py-01-visual-studio-publish-python-script-on-a-unix-machine-remote-debug/

```
$ sudo apt-get install samba samba-common-bin
$ sudo nano /etc/samba/smb.conf

[pythonapp]
path=/home/pi/WL-Monitor-Pi
browsable=yes
writable=yes
only guest=no
create mask=0777
directory mask=0777
public=yes
```

-> Enter in Windows Explorer: 

```
\\<ip address of your Raspberry Pi>\pythonapp
```


## Further Coding Instructions

- Adafruit LCD panel: https://github.com/adafruit/Adafruit_Python_CharLCD
- WL-Monitor-Pi original Python script: https://github.com/mabe-at/WL-Monitor-Pi

