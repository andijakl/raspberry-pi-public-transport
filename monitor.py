#!/usr/bin/python
import sys
import getopt
import time
import requests
import json
import Adafruit_CharLCD as LCD

# Visual Studio debugging
#import ptvsd
#ptvsd.enable_attach('wlmonitor')

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
	time1 = "N/A"
	time2 = None

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
	
	
	apiurl = 'https://www.wienerlinien.at/ogd_realtime/monitor?sender={apikey}';
	rblUrlPart = '&rbl={rblNum}';
	# Sleep time in seconds - wait time between requests
	# (note: uses half the time in case of a retry for an error)
	st = 10
	

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
	requestUrl = apiurl.replace('{apikey}', apikey)
	for addRblId in args:
		print('Adding rbl ID: ' + addRblId)
		tmprbl = RBL()
		tmprbl.id = int(addRblId)
		rbls.append(tmprbl)
		requestUrl += rblUrlPart.replace('{rblNum}', addRblId);
		
	# Start at exception count 1 so that exception is already shown if happening at startup
	# (otherwise, only 2nd exception is shown to keep successful times up longer)
	global exCount;
	exCount = 1;
		
	while True:
		try:
			r = requests.get(requestUrl, timeout=10);
			if r.status_code == requests.codes.ok:
				rjson = r.json()
				# Demo data for debugging
				#rjson = json.loads('{"data":{"monitors":[{"locationStop":{"type":"Feature","geometry":{"type":"Point","coordinates":[16.3691011072259,48.1785633982113]},"properties":{"name":"60200286","title":"Erlachplatz","municipality":"Wien","municipalityId":90001,"type":"stop","coordName":"WGS84","attributes":{"rbl":759}}},"lines":[{"name":"14A","towards":"Reumannplatz U","direction":"H","richtungsId":"1","barrierFree":true,"realtimeSupported":true,"trafficjam":false,"departures":{"departure":[{"departureTime":{"timePlanned":"2016-10-28T23:44:00.000+0200","timeReal":"2016-10-28T23:45:58.000+0200","countdown":8}}]},"type":"ptBusCity","lineId":414}],"attributes":{}}]},"message":{"value":"OK","messageCode":1,"serverTime":"2016-10-28T23:37:11.924+0200"}}');
				handleWlResponse(rjson, rbls);
			else:
				handleError("Bad response: " + str(r.status_code));
		except Exception as e:
			handleError(e);
					
		# Sleep until retry and check button press
		# Sleep for half the time if there was an exception (but only for exceptions 1...20 - if there are too many, keep normal wait time).
		sleepTime = st if (exCount < 1 or exCount > 20) else st / 2;
		for i in range(sleepTime):
			if lcd.is_pressed(LCD.SELECT): goodBye();
			if lcd.is_pressed(LCD.DOWN): 
				# Indicate that key was registered
				lcd.set_color(1.0, 1.0, 0.0);
				break;
			time.sleep(1);
			
	print ('Out of loop!')

def handleWlResponse(rjson, rbls):
	global exCount;
	# Check if we got lines at all
	numReturnedLines = len(rjson['data']['monitors']);
	if (numReturnedLines < 1):
		handleError("Response contains no lines");
	else:
		# Reset RBL departure data
		for curSavedRbl in rbls:
			curSavedRbl.time1 = "N/A";
			curSavedRbl.time2 = None;
		
		# Parse RBL data out of JSON
		for curRbl in rjson['data']['monitors']:
			# Parse individual RBL (contains departure info)
			parsedRbl = parseRbl(curRbl);
			# Check if we're waiting for data of this RBL
			for rblIdx in range(len(rbls)):
				if rbls[rblIdx].id == parsedRbl.id:
					# Found RBL in our list? -> Update (replace) the RBL object
					rbls[rblIdx] = parsedRbl;
					break;
			
		# Show successful info on LCD
		lcd.set_color(0.0, 1.0, 0.0);
		lcdShow(rbls);
		exCount = 0;
	
		
def goodBye():
	# Quit
	global lcd;
	lcd.set_color(1.0, 1.0, 1.0)
	lcd.set_backlight(0.0)
	lcd.clear()
	lcd.enable_display(False)
	sys.exit("Good bye!")

# Increases exception count and shows error message if the count >= 2
def handleError(e):
	global lcd;
	global exCount;
	exCount+=1;
	# Set screen to red in any case to indicate issues
	lcd.set_color(1.0, 0.0, 0.0)
	print( "Error: " + repr(e) )
	if (exCount >= 2):
		# More than two errors after each other? Show error message to user.
		# Insert newline after 16 chars, trim to 33 chars (16 * 2 + 1x \n)
		lcd.message(insertNewline(repr(e), 16)[:33]);
		
# Parse RBL objects out of the supplied JSON list 
def parseRbl(rjson):
	# New tmp RBL object
	tmprbl = RBL();
	tmprbl.id = rjson['locationStop']['properties']['attributes']['rbl']
	tmprbl.line = rjson['lines'][0]['name']
	tmprbl.station = rjson['locationStop']['properties']['title']
	tmprbl.direction = rjson['lines'][0]['towards']
	# Try to get countdown values
	try:
		tmprbl.time1 = rjson['lines'][0]['departures']['departure'][0]['departureTime']['countdown'];
		tmprbl.time2 = rjson['lines'][0]['departures']['departure'][1]['departureTime']['countdown']
	except IndexError:
		print("Index not found when parsing time from JSON - at least one countdown not available");
	return tmprbl;

# Show departure data on the LCD screen
def lcdShow(rbls):
	global lcd;
	lcd.clear()
	
	msg = "";
	line = 0;
	# Go through all available RBLs
	for curRbl in rbls:
		# New line for line 1+
		if line > 0:
			msg += '\n';
			
		# Line direction
		msg += replaceUmlaut(curRbl.direction [:7]) + ' ';
		
		# First departure (if available)
		if type(curRbl.time1) is int:
			msg += '{:2d}'.format(curRbl.time1);
		elif type(curRbl.time1) is str:
			msg += curRbl.time1;
			
		# Second departure (if available)
		if type(curRbl.time2) is int:
			msg += ' / {:2d}'.format(curRbl.time2);
		elif type(curRbl.time2) is str:
			msg += ' / ' + curRbl.time2;
			
		line += 1;
	
	lcd.message(msg);

# Insert a newline char into the string at the specified index
def insertNewline(string, index):
    return string[:index] + '\n' + string[index:]
				
def dumpRBL(rbl):
	print (rbl.line + ' ' + rbl.station)
	print (rbl.direction)
	print (str(rbl.time) + ' Min.')
	
def usage():
	print ('usage: ' + __file__ + ' [-h] [-t time] -k apikey rbl [rbl ...]\n')
	print ('arguments:')
	print ('  -k, --key=\tAPI key')
	print ('  rbl\t\tRBL number\n')
	print ('optional arguments:')
	print ('  -h, --help\tshow this help')
	print ('  -t, --time=\ttime between station updates in seconds, default 10')

if __name__ == "__main__":
	main(sys.argv[1:])
