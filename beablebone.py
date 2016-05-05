#!/usr/bin/python
import sys, serial
from time import *
import time
import datetime, string
import Adafruit_BBIO.UART as UART
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
import Adafruit_BBIO.ADC as ADC
import cv2
UART.setup("UART2")
# ssid="Roronoa ZORO"
# pwd="qwerty12345"
# Globals for WIFI Id and PWD.
ssid="Tenda"
pwd="hellobro"
IdentityString = "67890"

FILE = None

BAUD = 115200
SCNT = 0
# Globals for TCP connection IP-PORT.
servIP = "192.168.0.104"  # Server IP Address
servPort = 5555

REG_OFF = True
REG_ON = False
ser = serial.Serial( '/dev/ttyO2', BAUD, timeout=2.5, rtscts=False )

# Power Cycle ESP8266 - The RTS pin is used to control the 3.3V regulator.
print "Pwr Off - 3s"
ser.setRTS( REG_OFF )	# Turn off 3.3V power.
sleep( 3 )
print "Pwr On - 3s"
ser.setRTS( REG_ON )	# Turn on 3.3V power.
sleep( 3 )		# and wait for WiFi to stabablize.

# Defination to handle AT commanda. Learn AT commands first.
# sCmd = AT command, waitTm=time to wait for reply, STern=Terminator String.
def wifiCommand( sCmd, waitTm=1, sTerm='OK' ):
	lp = 0
	ret = ""
	print
	print "Cmd: %s" % sCmd
	ser.flushInput()
	ser.write( sCmd + "\r\n" )
	ret = ser.readline()	# Eat echo of command.
	#sleep( 0.2 )
	while( lp < waitTm ):
		while( ser.inWaiting() ):
			ret = ser.readline().strip( "\r\n" )
			print ret
			lp = 0
		if( ret == sTerm ): break
		#if( ret == 'ready' ): break
		if( ret == 'ERROR' ): break
		sleep( 1 )
		lp += 1
	return ret

# Function for Image capture. reply 1 for success. 0 otherwise.
def take_pic():
	camera_port = 0
	ramp_frames = 1
	try:
		camera = cv2.VideoCapture(camera_port)
		def get_image():
		 retval, im = camera.read()
		 return im
		 
		for i in xrange(ramp_frames):
			temp = get_image()
		print("Taking image...")
		camera_capture = get_image()
		print "here12345"
		file = "/var/lib/cloud9/BTP/pics/"+str(int(time.time()))+".png"
		if(cv2.imwrite(file, camera_capture)):
			print "CLICK"
			return 1
		else:
			print "NO click"
			return 0
	except:
		return 0

# Interepreator of Server's command. Trt to perform the task and genetare reply.
# reply format "ab" a=command acceptance status. b=command perform status. 0=fail, 1=success.
def interepretate(inp):
    reply=""
    leninp=len(inp)
    if(leninp%4!=0 and leninp!=2):
        reply="00"
        
    else:
        cm=inp[0:2]
        op=""
        param = []
        if(leninp>2):
            op=inp[2:4]
        i=4
        while(i<leninp):
            param.append(inp[i:(i+4)])
            i=i+4
        if(cm=="gp"):
            if(op=="dr"):
                if(len(param)>0):
                    try:
                        pin=int(param[0])
                        pins="P8_"+str(pin)
                        GPIO.setup(pins, GPIO.IN)
                        if GPIO.input(pins):
                            reply="110001"
                            print("high")
                        else:
                            reply="110000"
                            print("LOW")
                    except:
                        reply="10"
                else:
                	reply="10"
                print "dr"
            elif(op=="dw"):
                if(len(param)>1):
                    try:
                        pin=int(param[0])
                        pins="P8_"+str(pin)
                        val=int(param[1])
                        GPIO.setup(pins, GPIO.OUT)
                        if val==0:
                            GPIO.output(pins, GPIO.LOW)
                            reply="110000"
                            print("low")
                        else:
                            GPIO.output(pins, GPIO.HIGH)
                            reply="110001"
                            print("high")
                    except:
                        reply="10"
                else:
                    reply="10"
                print "dw"
            elif(op=="ar"):
                reply="10"
                print "ar"
            elif(op=="aw"):
                reply="10"
                print "aw"
            else:
                reply="10"
        elif(cm=="tp"):
        	if(take_pic()==0):
        		reply="10"
        	else:
        		reply="11"
        	print "tp"
        else:
            reply="00"
    print reply
    return inp+","+reply

# Following lines are to setup ESP8266 wifi module.
# Test if working, Connecct to wifi, connect to TCP server.
def wifiCheckRxStream():
	while( ser.inWaiting() ):
		s = ser.readline().strip( "\r\n" )

wifiCommand( "AT" )				# Should just return an 'OK'.
wifiCommand( "AT+CIPCLOSE" )			# Close any open connection.
wifiCommand( "AT+RST", 5, sTerm='ready' )	# Reset the radio. Returns with a 'ready'.
#wifiCommand( "AT+GMR" )			# Report firmware number.
wifiCommand( "AT+CWMODE=1" )			# Set mode to 'Sta'.
#wifiCommand( "AT+CWLAP", 10 )			# Scan for AP nodes. Returns SSID / RSSI.

# Connect wifi then connect to TCP
def setup_esp():
	s=""
	# Join Access Point given SSID and Passcode.
	while(s !="OK"):
	    s=wifiCommand( "AT+CWJAP=\""+ssid+"\",\""+pwd+"\"", 20 )
	    sleep(1)
	wifiCommand( "AT+CWJAP?" )
	
	
	# Sometimes it takes a couple querries until we get a IP number.
	sIP = wifiCommand( "AT+CIFSR", 3, sTerm="ERROR" )
	if( sIP == 'ERROR' ):
		i = 10	# Retry n times.
		while( (sIP == 'ERROR') and (i > 0) ):
			print i
			sIP = wifiCommand( "AT+CIFSR", 3, sTerm="ERROR" )
			if( sIP == 'ERROR' ): sleep( 3 )
			i -= 1
		if( i > 0 ):
			print "IP Num:", sIP
		else:
			print "Bad IP Number."
	else:
			print "IP Num:", sIP
	
	wifiCommand( "AT+CIPMUX=0" )	# Setup for single connection mode.
	print "Delay - 5s"
	sleep( 5 )
	
	s=""
	while (s != "OK"):
	    s = wifiCommand( "AT+CIPSTART=\"TCP\",\""+servIP+"\","+str(servPort), 10, sTerm="OK" )
	    sleep(1)

# Send Board's Identity to Server and wait for reply.
	#cmd = 'GET / HTTP/1.0\r\n\r\n'
	cmd = IdentityString
	#cmd = "Now is the time for all good men to come to the aid of their country.\r\n"
	#cmd = "Bridgeport 30 34 31 35 31 34 41 42 43 34\r\n"
	cmdLn = str( len(cmd) )
	s = wifiCommand( "AT+CIPSEND=" + cmdLn, sTerm=">" )
	#sleep( 1 )
	wifiCommand( cmd, sTerm="SEND OK" )
	sleep(0.5 )

	while( ser.inWaiting() ):
    		sys.stdout.write( ser.read() )
    		sys.stdout.flush()
	sleep( 0.2 )
	#wifiCommand( "+IPD" )
# 	i = 5
# 	while( i > 0 ):		# Dump whatever comes over the TCP link.
# 		while( ser.inWaiting() ):
# 			sys.stdout.write( ser.read() )
# 			#i = 5 	# Keep timeout reset as long as stuff in flowing.
# 			i=0
# 		sys.stdout.flush()
# 		#i -= 1
# 		sleep( 0.2 )
	print "1st loop over"
	# Connection is established now. Now wait for Server's command. Interepretate it. Send reply back to server.
setup_esp()
while 1:
		cmd=""
   		while( ser.inWaiting() ):
   			cmd += ser.read()
   		if(cmd.strip()=="CLOSED"):
   			print "here123"
   			setup_esp()
   		cmd_split=cmd.split(':')
   		if(len(cmd_split)==2):
   		    print cmd_split[1]
   		    reply=interepretate(cmd_split[1])
   		    repln = str( len(reply) )
   		    s = wifiCommand( "AT+CIPSEND=" + repln, sTerm=">" )
   		    wifiCommand( reply, sTerm="SEND OK" )
			#sleep(0.5)
   		#sys.stdout.flush()
   		#sleep( 0.2 )

# else:
#         print "in else now "
#         print "Error:>>"
#     	ser.write( "\r\n" )
#     	sleep( 0.5 )
#     	i = 5
#     	while( (i > 0) and ser.inWaiting() ):	# Dump whatever is in the Rx buffer.
#     		while( ser.inWaiting() ):
#     			sys.stdout.write( ser.read() )
#     			i = 5 	# Keep timeout reset as long as stuff in flowing.
#     		sys.stdout.flush()
#     		i -= 1
#     		sleep( 1 )
