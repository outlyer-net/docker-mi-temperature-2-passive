#!/usr/bin/python3

from bluepy import btle
import argparse
import os
import re
from dataclasses import dataclass
from collections import deque
import threading
import time
import signal
import traceback
import math


@dataclass
class Measurement:
	temperature: float
	humidity: int
	calibratedHumidity: int = 0
	battery: int = 0
	timestamp: int = 0

	def __eq__(self, other):
		if self.temperature == other.temperature and self.humidity == other.humidity and self.calibratedHumidity == other.calibratedHumidity and self.battery == other.battery:
			return  True
		else:
			return False

measurements=deque()
globalBatteryLevel=0
previousMeasurement=Measurement(0,0,0,0)
identicalCounter=0

def signal_handler(sig, frame):
        os._exit(0)

def thread_SendingData():
	global previousMeasurement
	global measurements
	path = os.path.dirname(os.path.abspath(__file__))
	while True:
		try:
			mea = measurements.popleft()
			if (mea == previousMeasurement and identicalCounter < args.skipidentical): #only send data when it has changed or X identical data has been skipped, ~10 pakets per minute, 50 pakets --> writing at least every 5 minutes
				print("Measurements are identical don't send data\n")
				identicalCounter+=1
				continue
			identicalCounter=0
			fmt = "sensorname,temperature,humidity" #don't try to seperate by semicolon ';' os.system will use that as command seperator
			params = args.name + " " + str(mea.temperature) + " " + str(mea.humidity)
			if (args.TwoPointCalibration or args.offset): #would be more efficient to generate fmt only once
				fmt +=",humidityCalibrated"
				params += " " + str(mea.calibratedHumidity)
			if (args.battery):
				fmt +=",batteryLevel"
				params += " " + str(mea.battery)
			params += " " + str(mea.timestamp)
			fmt +=",timestamp"
			cmd = path + "/" + args.callback + " " + fmt + " " + params
			print(cmd)
			ret = os.system(cmd)
			if (ret != 0):
					measurements.appendleft(mea) #put the measurement back
					print ("Data couln't be send to Callback, retrying...")
					time.sleep(5) #wait before trying again
			else: #data was sent
				previousMeasurement=Measurement(mea.temperature,mea.humidity,mea.calibratedHumidity,mea.battery,0) #using copy or deepcopy requires implementation in the class definition

		except IndexError:
			#print("Keine Daten")
			time.sleep(1)
		except Exception as e:
			print(e)
			print(traceback.format_exc())

mode="round"
class MyDelegate(btle.DefaultDelegate):
	def __init__(self, params):
		btle.DefaultDelegate.__init__(self)
		# ... initialise here
	
	def handleNotification(self, cHandle, data):
		global measurements
		try:
			measurement = Measurement(0,0,0,0,0)
			measurement.timestamp = int(time.time())
			temp=int.from_bytes(data[0:2],byteorder='little')/100
			#print("Temp received: " + str(temp))
			if args.round:
				#print("Temperatur unrounded: " + str(temp
				
				if args.debounce:
					global mode
					temp*=10
					intpart = math.floor(temp)
					fracpart = round(temp - intpart,1)
					#print("Fracpart: " + str(fracpart))
					if fracpart >= 0.7:
						mode="ceil"
					elif fracpart <= 0.2: #either 0.8 and 0.3 or 0.7 and 0.2 for best even distribution
						mode="trunc"
					#print("Modus: " + mode)
					if mode=="trunc": #only a few times
						temp=math.trunc(temp)
					elif mode=="ceil":
						temp=math.ceil(temp)
					else:
						temp=round(temp,0)
					temp /=10.
					#print("Debounced temp: " + str(temp))
				else:
					temp=round(temp,1)
			humidity=int.from_bytes(data[2:3],byteorder='little')
			print("Temperature: " + str(temp))
			print("Humidity: " + str(humidity))
			measurement.temperature = temp
			measurement.humidity = humidity

			if args.offset:
				humidityCalibrated = humidity + args.offset
				print("Calibrated humidity: " + str(humidityCalibrated))
				measurement.calibratedHumidity = humidityCalibrated

			if args.TwoPointCalibration:
				offset1=args.offset1
				offset2=args.offset2
				p1y=args.calpoint1
				p2y=args.calpoint2
				p1x=p1y - offset1
				p2x=p2y - offset2
				m = (p1y - p2y) * 1.0 / (p1x - p2x) # y=mx+b
				#b = (p1x * p2y - p2x * p1y) * 1.0 / (p1y - p2y)
				b = p2y - m * p2x #would be more efficient to do this calculations only once
				humidityCalibrated=m*humidity + b
				if (humidityCalibrated > 100 ): #with correct calibration this should not happen
					humidityCalibrated = 100
				elif (humidityCalibrated < 0):
					humidityCalibrated = 0
				humidityCalibrated=int(round(humidityCalibrated,0))
				print("Calibrated humidity: " + str(humidityCalibrated))
				measurement.calibratedHumidity = humidityCalibrated

			if args.battery:
				measurement.battery = globalBatteryLevel

			measurements.append(measurement)

		except Exception as e:
			print("Fehler")
			print(e)
			print(traceback.format_exc())
		
# Initialisation  -------

def connect():
	p = btle.Peripheral(adress)	
	val=b'\x01\x00'
	p.writeCharacteristic(0x0038,val,True)
	p.withDelegate(MyDelegate("abc"))
	return p

# Main loop --------
parser=argparse.ArgumentParser()
parser.add_argument("--device","-d", help="Set the device MAC-Address in format AA:BB:CC:DD:EE:FF")
parser.add_argument("--battery","-b", help="Read batterylevel every x update", metavar='N', type=int)
parser.add_argument("--round","-r", help="Round temperature to one decimal place",action='store_true')
parser.add_argument("--name","-n", help="Give this sensor a name, used at callback function")
parser.add_argument("--callback","-call", help="Pass the path to a program/script that will be called on each new measurement")
parser.add_argument("--skipidentical","-skip", help="N consecutive identical measurements won't be reported to callbackfunction",metavar='N', type=int, default=0)
parser.add_argument("--debounce","-deb", help="Enable this option for storing temperature with less noise",action='store_true')

offsetgroup = parser.add_argument_group("Offset calibration mode")
offsetgroup.add_argument("--offset","-o", help="Enter an offset to the humidity value read",type=int)

complexCalibrationGroup=parser.add_argument_group("2 Point Calibration")
complexCalibrationGroup.add_argument("--TwoPointCalibration","-2p", help="Use complex calibration mode. All arguments below are required",action='store_true')
complexCalibrationGroup.add_argument("--calpoint1","-p1", help="Enter the first calibration point",type=int)
complexCalibrationGroup.add_argument("--offset1","-o1", help="Enter the offset for the first calibration point",type=int)
complexCalibrationGroup.add_argument("--calpoint2","-p2", help="Enter the second calibration point",type=int)
complexCalibrationGroup.add_argument("--offset2","-o2", help="Enter the offset for the second calibration point",type=int)

args=parser.parse_args()
if args.device:
	if re.match("[0-9a-fA-F]{2}([:]?)[0-9a-fA-F]{2}(\\1[0-9a-fA-F]{2}){4}$",args.device):
		adress=args.device
	else:
		print("Please specify device MAC-Address in format AA:BB:CC:DD:EE:FF")
		os._exit(1)
else:
	parser.print_help()
	os._exit(1)

if args.TwoPointCalibration:
	if(not(args.calpoint1 and args.offset1 and args.calpoint2 and args.offset2)):
		print("In 2 Point calibration you have to enter 4 points")
		os._exit(1)
	elif(args.offset):
		print("Offset calibration and 2 Point calibration can't be used together")
		os._exit(1)
if not args.name:
	args.name = args.device

p=btle.Peripheral()
cnt=0

if args.callback:
	signal.signal(signal.SIGINT, signal_handler)
	dataThread = threading.Thread(target=thread_SendingData)
	dataThread.start()
	
connected=False

while True:
	try:
		if not connected:
			print("Trying to connect to " + adress)
			p=connect()
			connected=True
		if p.waitForNotifications(2000):
			# handleNotification() was called
			if args.battery:
				if(cnt % args.battery == 0):
					batt=p.readCharacteristic(0x001b)
					batt=int.from_bytes(batt,byteorder="little")
					print("Battery-Level: " + str(batt))
					globalBatteryLevel = batt
			cnt += 1
			print("")
			continue
	except:
		print("Connection lost")
		connected=False
		
	print ("Waiting...")
	# Perhaps do something else here