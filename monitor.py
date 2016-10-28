#!/usr/bin/python
import sys
import getopt
import time
import requests
import Adafruit_CharLCD as LCD

reload(sys)
sys.setdefaultencoding('latin1')

# Get API key from: https://www.wien.gv.at/formularserver2/user/formular.aspx?pid=3b49a23de1ff43efbc45ae85faee31db&pn=B0718725a79fb40f4bb4b7e0d2d49f1d1
# Get RBL numbers from: https://till.mabe.at/rbl/
# run with: python monitor.py -k <API-key> <rbl-1> <rbl-2>

class RBL:
	id = 0
	line = ''
	station = ''
	direction = ''
	time1 = -1
	time2 = -1

def replaceUmlaut(s):
	s = s.replace(chr(196), "Ae") # A umlaut
	s = s.replace(chr(214), "Oe") # O umlaut
	s = s.replace(chr(220), "Ue") # U umlaut
	s = s.replace(chr(228), "ae") # a umlaut
	s = s.replace(chr(223), "ss") # Sharp s
	s = s.replace(chr(246), "oe") # o umlaut
	s = s.replace(chr(252), "ue") # u umlaut
	return s

def main(argv):
	
	global lcd 
	lcd = LCD.Adafruit_CharLCDPlate()
	lcd.enable_display(True)
	lcd.set_color(0.0, 0.0, 1.0)
	lcd.set_backlight(1.0)
	lcd.clear()
	
	
	apiurl = 'https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl0}&rbl={rbl1}&sender={apikey}'
	st = 20
	

	try:                                
		opts, args = getopt.getopt(argv, "hk:t:", ["help", "key=", "time="])
	except getopt.GetoptError:          
		usage()                         
		sys.exit(2)                     
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()                     
			sys.exit()                                    
		elif opt in ("-k", "--key"):
			apikey = arg
		elif opt in ("-t", "--time"):
			try:
				tmpst = int(arg)
				if tmpst > 0:
					st = tmpst
			except ValueError:
				usage()
				sys.exit(2)


	if apikey == False or len(args) < 1:
		usage()
		sys.exit()
	
	rbls = []
	for rbl in args:
		print('adding rbl ' + rbl)
		tmprbl = RBL()
		tmprbl.id = rbl
		rbls.append(tmprbl)
		
	# Start at exception count 1 so that exception is already shown if happening at startup
	# (otherwise, only 2nd exception is shown to keep successful times up longer)
	exCount = 1;
	
	while True:
		url = apiurl.replace('{apikey}', apikey).replace('{rbl0}', rbls[0].id).replace('{rbl1}', rbls[1].id)
		try:
			r = requests.get(url)
			if r.status_code == 200:
				rjson = r.json()
				# TODO: optimize this code a bit...
				# TODO: improve error handling, e.g., if only one departure can be retrieved or if service is unavailable.
				rbls[0].line = rjson['data']['monitors'][0]['lines'][0]['name']
				rbls[0].station = rjson['data']['monitors'][0]['locationStop']['properties']['title']
				rbls[0].direction = rjson['data']['monitors'][0]['lines'][0]['towards']
				rbls[0].time1 = rjson['data']['monitors'][0]['lines'][0]['departures']['departure'][0]['departureTime']['countdown']
				rbls[0].time2 = rjson['data']['monitors'][0]['lines'][0]['departures']['departure'][1]['departureTime']['countdown']
				rbls[1].line = rjson['data']['monitors'][1]['lines'][0]['name']
				rbls[1].station = rjson['data']['monitors'][1]['locationStop']['properties']['title']
				rbls[1].direction = rjson['data']['monitors'][1]['lines'][0]['towards']
				rbls[1].time1 = rjson['data']['monitors'][1]['lines'][0]['departures']['departure'][0]['departureTime']['countdown']
				rbls[1].time2 = rjson['data']['monitors'][1]['lines'][0]['departures']['departure'][1]['departureTime']['countdown']
				lcd.set_color(0.0, 1.0, 0.0)
				lcdShow(rbls[0],rbls[1])
				exCount = 0;
		except Exception as e:
			exCount += 1;
			handleError(exCount, e);
					
		# Sleep until retry and check button press
		if lcd.is_pressed(LCD.SELECT): goodBye()
		if (exCount < 1 or exCount > 20):
			# Sleep for half the time if there was an exception (but only for exceptions 1...20 - if there are too many, keep normal wait time).
			time.sleep(st/2)
		if lcd.is_pressed(LCD.SELECT): goodBye()
		time.sleep(st/2)
	
	print ('Out of loop!')

def goodBye():
	# Quit
	global lcd;
	lcd.set_color(1.0, 1.0, 1.0)
	lcd.set_backlight(0.0)
	lcd.clear()
	lcd.enable_display(False)
	sys.exit("Good bye!")

def handleError(exCount, e):
	global lcd;
	lcd.set_color(1.0, 0.0, 0.0)
	print( "Error: " + repr(e) )
	if (exCount >= 2):
		# More than two errors after each other? Show error message to user.
		# Insert newline after 16 chars, trim to 33 chars (16 * 2 + 1x \n)
		lcd.message(insertNewline(repr(e), 16)[:33]);

def lcdShow(rbl0,rbl1):
	global lcd;
	lcd.clear()
	lcd.message(replaceUmlaut(rbl0.direction [:7] + ' {:2d}'.format(rbl0.time1) + ' / ' + '{:2d}'.format(rbl0.time2) + '\n' + 
				rbl1.direction [:7] + ' {:2d}'.format(rbl1.time1) + ' / ' + '{:2d}'.format(rbl1.time2)))

def insertNewline(string, index):
    return string[:index] + '\n' + string[index:]
	
def usage():
	print ('usage: ' + __file__ + ' [-h] [-t time] -k apikey rbl1 rbl2\n')
	print ('arguments:')
	print ('  -k, --key=\tAPI key')
	print ('  rbl\t\tRBL number\n')
	print ('optional arguments:')
	print ('  -h, --help\tshow this help')
	print ('  -t, --time=\ttime between station updates in seconds, default 10')

if __name__ == "__main__":
	main(sys.argv[1:])
