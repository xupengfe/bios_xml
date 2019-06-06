#Description:
#  The Input to the Aakruti app is the path to the folder which contains the Configuration XML files.
#  1. The drawing screen gets cleared if there are previous drawings.
#  2. Parse the XML with following information and store it in database of respective classes.
#    2.1 Parse Topology section to get Socket information and Port connections
#    2.2 Parse Dimm-info section to get Dimm information
#    2.3 Parse the pci-devices section to information about bus,device and function
#    2.4 Also store PCH information
#  3. Calculate the boundaries for Socket,Dimms,PCH,Devices and Bridges based on drawing area.
#    3.1 Uses Turtle to draw the objects.
#    3.2 We tried drawing objects parrallely by Multi-Threading to speed up the execution,
#        but looks like turtle cannot handle Multi-Threaded operation
#  4. Draw the Objects in the following order.
#    4.1 Draw socket and connected Dimms, Buses, Devices and Bridges
#    4.2 Draw the port connections connecting the sockets.
#
# Version = 0.5    Initial Version.
__author__ = 'ashinde'
from turtle import *
from Tkinter import *
import turtle, threading, operator, time, string, math, glob
import xml.etree.ElementTree as ET

CardsDict = {	0x85A010B5 : "Kfir Switch Upstream Port",
				0x851810B5 : "Kfir Switch Downstream Port",
				0x85D110B5 : "Kfir NT port (Virual)",
				0x85D010B5 : "Kfir Upload port (KHC)",
				0x86A010B5 : "Kfir NT port",
				0x81A210B5 : "Kfir PCIe2PCI Bridge (8111)",
				0x811110b5 : "PCI Express bridge PEX8111",
				0x905410B5 : "USBX",
				0x53748086 : "HAVC5",
				0x53758086 : "CORIN",
				0x76478086 : "Snir X",
				0x76488086 : "Snir 3",
				0x76498086 : "SnirCnaan",
				0x21548086 : "OPAL",
				0x12368086 : "Barkan",
				0x82A010B5 : "LotemTarget86E1Bridge",
				0x82A110b5 : "Sinai",
				0x82D08086 : "Masada",
				0x82D18086 : "Lotem",
				0x82D38086 : "GTx",
				0xF1178086 : "Stealth",
				0x82A210B5 : "Kfir KTC",
				0x228017CC : "USBNet2280",
				0x228217CC : "USBNet2282",
				0x0522102B : "VGA Card",
				0x10D38086 : "NIC"}

SIZE_X = SIZE_Y = basePointx = basePointy = DISTANCE_BETWEEN_BUSES = DISTANCE_BETWEEN_SLOTS = DISTANCE_BETWEEN_PORTS = BUS_LENGTH = BUS_THICKNESS = 0
CPU_BOX_X = CPU_BOX_Y = CPU_FONT = CPU_THICKNESS = QPI_LENGTH = QPI_FONT = QPI_SPEED_FONT = QPI_THICKNESS = DIMM_LENGTH = DIMM_BREADTH = DIMM_FONT = DIMM_INFO_FONT = 0
BRIDGE_LENGTH = BRIDGE_BREADTH = BRIDGE_FONT = BRIDGE_INFO_FONT = DEVICE_LENGTH = NO_OF_CHARACTERS_OF_FUNCTION = DEVICE_INFO_FONT = DEVICE_THICKNESS = 0
PCH_BREADTH = PCH_FONT = PCH_THICKNESS = CHANNEL_THICKNESS = CHANNEL_LENGTH = CHANNEL_FONT = DISPLAY_BIOS_INFO_FONT = 0
window = printTurtle = pch = textData = socketDict = None
INFO_FLAG = False
SOCKET_COLOR = DIMM_COLOR = DEVICE_COLOR = PCH_COLOR = BRIDGE_COLOR = ""

def initializeScreen():
	global SIZE_X, SIZE_Y, basePointx, basePointy, DISTANCE_BETWEEN_BUSES, DISTANCE_BETWEEN_SLOTS, DISTANCE_BETWEEN_PORTS, BUS_LENGTH, BUS_THICKNESS
	global CPU_BOX_X, CPU_BOX_Y, CPU_FONT, CPU_THICKNESS, QPI_LENGTH, QPI_FONT, QPI_SPEED_FONT, QPI_THICKNESS, DIMM_LENGTH, DIMM_BREADTH, DIMM_FONT, DIMM_INFO_FONT
	global BRIDGE_LENGTH, BRIDGE_BREADTH, BRIDGE_FONT, BRIDGE_INFO_FONT, DEVICE_LENGTH, DEVICE_BREADTH, DEVICE_FONT, NO_OF_CHARACTERS_OF_FUNCTION, FUNC_NAME_FONT, DEVICE_INFO_FONT, DEVICE_THICKNESS, DISPLAY_BIOS_INFO_FONT
	global PCH_BREADTH, PCH_FONT, PCH_THICKNESS, CHANNEL_LENGTH, CHANNEL_THICKNESS, CHANNEL_FONT
	global window, printTurtle, pch, textData, socketDict
	global INFO_FLAG
	global SOCKET_COLOR, DIMM_COLOR, DEVICE_COLOR, PCH_COLOR, BRIDGE_COLOR

	window = turtle.Screen()
	window.bgcolor("lightblue")
	window.title("Aakruti V0.5")
	window.setup(width = 1.0, height = 1.0, startx = 0, starty = 0)

	SIZE_X = window.window_width()
	SIZE_Y = window.window_height()
	basePointx = -(0.3125*SIZE_X)
	basePointy = SIZE_Y/10
	DISPLAY_BIOS_INFO_FONT = SIZE_Y/50

	DISTANCE_BETWEEN_BUSES = SIZE_X/25
	DISTANCE_BETWEEN_SLOTS = SIZE_Y/25
	DISTANCE_BETWEEN_PORTS = SIZE_Y/20

	BUS_LENGTH = 0.03*SIZE_Y
	BUS_THICKNESS = 2

	CPU_BOX_X = SIZE_X/10
	CPU_BOX_Y = SIZE_Y/8
	CPU_FONT = CPU_BOX_Y/7
	SOCKET_COLOR = "yellow"
	CPU_THICKNESS = 5

	QPI_LENGTH = SIZE_X/10               #Distance between sockets
	QPI_FONT = CPU_BOX_Y/10
	QPI_SPEED_FONT = QPI_LENGTH/15
	QPI_THICKNESS = 3

	DIMM_LENGTH = SIZE_X/12
	DIMM_BREADTH = SIZE_Y/30
	DIMM_COLOR = "green"
	DIMM_FONT = DIMM_BREADTH/2
	DIMM_INFO_FONT = 10

	BRIDGE_LENGTH = DISTANCE_BETWEEN_BUSES
	BRIDGE_BREADTH = SIZE_Y/30
	BRIDGE_COLOR = "darkorange"
	BRIDGE_FONT = BRIDGE_BREADTH/2
	BRIDGE_INFO_FONT = 10

	DEVICE_LENGTH = SIZE_X/30
	DEVICE_BREADTH = SIZE_Y/30
	DEVICE_COLOR = "orange"
	DEVICE_FONT = DEVICE_BREADTH/3
	NO_OF_CHARACTERS_OF_FUNCTION = 6
	FUNC_NAME_FONT = (5*DEVICE_LENGTH)/(4*NO_OF_CHARACTERS_OF_FUNCTION)
	DEVICE_INFO_FONT = 10
	DEVICE_THICKNESS = 1

	PCH_BREADTH = SIZE_Y/25
	PCH_COLOR = "violet"
	PCH_FONT = PCH_BREADTH/3
	PCH_THICKNESS = 2
	##Font sizes

	CHANNEL_THICKNESS = 2
	CHANNEL_LENGTH = SIZE_X/12
	NO_OF_CHARACTERS_ON_CHANNEL = 16
	CHANNEL_FONT = (5*CHANNEL_LENGTH)/(NO_OF_CHARACTERS_ON_CHANNEL*4)

	INFO_FLAG = False   ##For On-click event handling
	printTurtle = turtle.Turtle() ##Global turtle for on-click event
	printTurtle.speed(0)
	textData = [] ##Data to be displayed on-click

	socketDict = dict()
	pch = None

class Socket:
	'This is a Socket class'
	def __init__(self,id,type,platformName):
		self.platformName = platformName
		self.socketId = id
		self.type = type
		self.minBus = 0
		self.maxBus = 0
		self.ports = []
		self.controllers = []
		self.channelIndex = 0
		self.buses = {}
		self.activeBuses = 0.0
		self.startPoint = Point(0,0)
		self.nextHPort = 0      #Horizontal port count while drawing
		self.nextVPort = 0      #Vertical port count while drawing
		self.nextBusPoint = 0.0   #Index of bus to be drawn
		self.noOfBridgeBuses = 0
		self.socketLength = 2.0*DISTANCE_BETWEEN_BUSES ##Default length assuming socket has 2 buses on average
		self.socketBreadth = 3*DISTANCE_BETWEEN_SLOTS ##Default breadth assuming socket has 3 dimm slots on average

	def setSocketStartPoint(self):
		x = basePointx
		y = basePointy
		if (self.socketId == 0):
			self.startPoint = Point( x , y )
		elif (self.socketId == 1):
			self.startPoint = Point( (x + self.socketLength + QPI_LENGTH) , y )
		elif (self.socketId == 2):
			self.startPoint = Point( x , (y - self.socketBreadth - QPI_LENGTH) )
		else:
			self.startPoint = Point( (x + self.socketLength + QPI_LENGTH) , (y - self.socketBreadth - QPI_LENGTH) )

	def setSocketDimension(self):
		dimmCount = 0
		if (self.activeBuses > 2):
			self.socketLength = self.socketLength + ((self.activeBuses-2)*DISTANCE_BETWEEN_BUSES)
		if (self.socketId == 0):
			self.socketLength = self.socketLength + ((len(pch.busNumbers)/2+1)*DISTANCE_BETWEEN_BUSES) ## reserve space for PCH bus
		for controller in self.controllers:
			for channel in controller.channels:
				dimmCount += len(channel.dimmSlots)
		if (dimmCount > 3):
			self.socketBreadth = self.socketBreadth + ((dimmCount-3)*DISTANCE_BETWEEN_SLOTS)

	def setActiveBusesCount(self):
		for bus in self.buses.values():
			if( (isActiveBus(self,bus)) and (bus.busId not in pch.busNumbers) ):
				self.activeBuses += 1.0

	def drawSocket(self):
		drawRectangle(self.socketLength, self.socketBreadth, self.startPoint.x, self.startPoint.y, ("CPU"+str(self.socketId)), CPU_FONT, SOCKET_COLOR, "bold", CPU_THICKNESS)

	def displaySocket(self):
		print "Socket ID:%d" %self.socketId
		print "Type:"+self.type
		for port in self.ports:
			port.displayPort()
		for controller in self.controllers:
			controller.displayController()
		for busKey in self.buses.keys():
			self.buses.get(busKey).displayBus()

class Port:
	'This is a Port class'
	def __init__(self,number,speed,to_socket,to_port):
		self.portNumber = number
		self.speed = speed
		self.to_socket = to_socket
		self.to_port = to_port
		self.isDrawn = False
		self.isCalculated = False
		self.portPoint = Point(0, 0)

	def setPortPoint(self,sockt):
		baseX = sockt.startPoint.x
		baseY = sockt.startPoint.y
		x = y = 0

		##Fetch the destination port
		to_sockt = socketDict.get(self.to_socket)
		for prt in to_sockt.ports:
			if (prt.portNumber == self.to_port):
				to_port = prt
				break

		portText = "QPI-P" + str(self.portNumber)
		to_port.isCalculated = True

		if ( sockt.socketId == 0 ):
			if ( self.to_socket == 1 ):
				x = baseX + sockt.socketLength
				y = baseY - (((sockt.nextHPort+1)*sockt.socketBreadth)/3)
				drawText(None, portText, (x - (0.8*QPI_FONT*len(portText))), (y-(sockt.nextHPort * QPI_FONT)), QPI_FONT)
				to_port.portPoint = Point(to_sockt.startPoint.x, y)
				drawText(None, "QPI-P" + str(self.to_port), (to_sockt.startPoint.x+(0.8*QPI_FONT)), y-(sockt.nextHPort * QPI_FONT), QPI_FONT)
				drawText(None, self.speed, x + (QPI_LENGTH/3), y + QPI_SPEED_FONT, QPI_SPEED_FONT)
				sockt.nextHPort = sockt.nextHPort + 1
				to_sockt.nextHPort = to_sockt.nextHPort + 1
			elif ( self.to_socket == 2 ):
				x = baseX + sockt.socketLength - (DISTANCE_BETWEEN_PORTS*(sockt.nextVPort+1)) - (2*QPI_FONT)
				y = baseY - sockt.socketBreadth
				drawText(None, portText, x-5, y+2, QPI_FONT)
				sockt.nextVPort = sockt.nextVPort + 1
				to_port.portPoint = Point(x , to_sockt.startPoint.y)
				drawText(None, "QPI-P" + str(self.to_port), x-5, (to_sockt.startPoint.y-(QPI_FONT*2)), QPI_FONT)
				drawText(None, self.speed, x+5, (y-(QPI_LENGTH/2)), QPI_SPEED_FONT)
				to_sockt.nextVPort = to_sockt.nextVPort+1
			else:
				x = baseX + sockt.socketLength
				y = baseY - (((sockt.nextHPort+1)*sockt.socketBreadth)/3)
				drawText(None, portText, x - (0.8*QPI_FONT*len(portText)), y - (sockt.nextHPort * QPI_FONT), QPI_FONT)
				to_port.portPoint = Point(to_sockt.startPoint.x, to_sockt.startPoint.y - (((to_sockt.nextHPort+1)*to_sockt.socketBreadth)/3))
				drawText(None, "QPI-P"+str(to_port.portNumber), to_port.portPoint.x+3, to_port.portPoint.y-(to_sockt.nextHPort * QPI_FONT), QPI_FONT)
				drawText(None, self.speed, (x + (QPI_LENGTH/3) - 10), (y - (QPI_LENGTH/3) - 10), QPI_SPEED_FONT)
				sockt.nextHPort = sockt.nextHPort + 1
				to_sockt.nextHPort = to_sockt.nextHPort + 1

		if (sockt.socketId == 1):
			if (self.to_socket == 2):
				x = baseX
				y = baseY - (((sockt.nextHPort+1)*sockt.socketBreadth)/3)
				drawText(None, portText, x+5, y-(sockt.nextHPort*QPI_FONT), QPI_FONT)
				to_port.portPoint = Point( (to_sockt.startPoint.x + to_sockt.socketLength) , to_sockt.startPoint.y - (((to_sockt.nextHPort+1)*to_sockt.socketBreadth)/3))
				drawText(None, "QPI-P"+str(to_port.portNumber), to_port.portPoint.x-(4.8*QPI_FONT), to_port.portPoint.y - (to_sockt.nextHPort*QPI_FONT), QPI_FONT)
				drawText(None, self.speed, (x - (QPI_LENGTH/3) + 10), (baseY - sockt.socketBreadth - (QPI_LENGTH/4) - QPI_SPEED_FONT), QPI_SPEED_FONT)
				sockt.nextHPort = sockt.nextHPort + 1
				to_sockt.nextHPort = to_sockt.nextHPort + 1
			else: #for port 3
				x = baseX + DISTANCE_BETWEEN_PORTS*(sockt.nextVPort+1)
				y = baseY - sockt.socketBreadth
				sockt.nextVPort = sockt.nextVPort+1
				drawText(None, portText, x-5, y+2, QPI_FONT)
				to_port.portPoint = Point(x, to_sockt.startPoint.y)
				drawText(None, "QPI-P"+str(to_port.portNumber), to_port.portPoint.x-5, to_port.portPoint.y-(2*QPI_FONT), QPI_FONT)
				drawText(None, self.speed,x+5, y-(QPI_LENGTH/2), QPI_SPEED_FONT)
				to_sockt.nextVPort = to_sockt.nextVPort+1

		if (sockt.socketId == 2): #for connection 2 to 3
			x = baseX + sockt.socketLength
			y = baseY - (((sockt.nextHPort+1)*sockt.socketBreadth)/3)
			y = baseY - ((2*sockt.socketBreadth)/3) - QPI_FONT
			drawText(None, portText, x-(0.8*QPI_FONT*len(portText)), y-QPI_FONT, QPI_FONT)
			to_port.portPoint = Point(to_sockt.startPoint.x, y)
			drawText(None, "QPI-P"+str(to_port.portNumber), to_port.portPoint.x+5, (to_port.portPoint.y-(QPI_FONT)), QPI_FONT)
			drawText(None, self.speed, x+(QPI_LENGTH/3), y+QPI_SPEED_FONT, QPI_SPEED_FONT)
			sockt.nextHPort = sockt.nextHPort + 1
			to_sockt.nextHPort = to_sockt.nextHPort + 1
		self.portPoint = Point(x, y)

	def draw_portConnection(self, sockt):
		from_port = self
		from_socket = sockt
		to_sockt = socketDict.get(self.to_socket)
		for prt in to_sockt.ports:
			if (prt.portNumber == self.to_port):
				to_port = prt
				to_port.isDrawn = True
				break
		drawLine(from_port.portPoint.x, from_port.portPoint.y, to_port.portPoint.x, to_port.portPoint.y, "black", QPI_THICKNESS)
		return

	def displayPort(self):
		print "Port Number: %d"%self.portNumber
		print "To socket: %d" %self.to_socket
		print "To port: %d"%self.to_port

class Controller:
	'This is a Controller class'
	def __init__(self,controllerID):
		self.controllerID = controllerID
		self.channels = []

	def displayController(self):
		print "Controller ID:"+self.controllerID
		for channel in self.channels:
			channel.displayChannel()

class Channel:
	'This is a Channel class'
	def __init__(self,num):
		self.channelNumber = num
		self.dimmIndex = 0      ##For drawing purpose
		self.dimmSlots = []

	def displayChannel(self):
		print "Channel Number:%d"%self.channelNumber
		print "Dimm Index:%d"%self.dimmIndex
		for dimm in self.dimmSlots:
			dimm.displayDimmSlot()

class DimmSlot:
	def __init__(self, slotNo, size, vendorName):
		self.slotNo = slotNo
		self.size = size
		self.vendorName = vendorName
		self.channelPoint = Point(0, 0)

	def setChannelPoint(self,sockt,controller,channel):
		baseX = sockt.startPoint.x
		baseY = sockt.startPoint.y
		if (len(channel.dimmSlots) == 1):
			if (sockt.socketId%2 == 0):
				x = baseX - CHANNEL_LENGTH - DIMM_LENGTH
				y = baseY - DISTANCE_BETWEEN_SLOTS*(sockt.channelIndex)
			else:
				x = baseX + sockt.socketLength + CHANNEL_LENGTH
				y = baseY - DISTANCE_BETWEEN_SLOTS*(sockt.channelIndex)
			sockt.channelIndex += 1
		else:     ##If channel has more than 1 dimmSlots
			if ((sockt.socketId%2) == 0):
				x = baseX - CHANNEL_LENGTH - DIMM_LENGTH
				y = baseY - DISTANCE_BETWEEN_SLOTS*(sockt.channelIndex)
			else:
				x = baseX + sockt.socketLength + CHANNEL_LENGTH
				y = baseY - DISTANCE_BETWEEN_SLOTS*(sockt.channelIndex)
			sockt.channelIndex += 1              
		self.channelPoint = Point(x, y)

	def draw_channel(self, sockt, controller, channel):
		x = self.channelPoint.x
		y = self.channelPoint.y
		drawRectangle(DIMM_LENGTH, DIMM_BREADTH, x, y, ("DDR "+str(self.size/1000)+"GB"), DIMM_FONT,DIMM_COLOR, "normal", CHANNEL_THICKNESS)
		if ((sockt.socketId%2) == 0):
			lineSrc = Point((x+DIMM_LENGTH), (y-(DIMM_BREADTH/2)))
			lineDest = Point(sockt.startPoint.x, (y-(DIMM_BREADTH/2)))
			drawText(None, ("MC%d, CH%d, Slot%d" %(eval(controller.controllerID), channel.channelNumber, self.slotNo)), (x+DIMM_LENGTH+(2*CHANNEL_FONT)), (y-CHANNEL_FONT), CHANNEL_FONT)
		else:
			lineSrc = Point(x, y -(DIMM_BREADTH/2))
			lineDest = Point( (sockt.startPoint.x+sockt.socketLength), y-(DIMM_BREADTH/2))
			drawText(None, ("MC%d, CH%d, Slot%d" %(eval(controller.controllerID), channel.channelNumber, self.slotNo)), (sockt.startPoint.x+sockt.socketLength+(2*CHANNEL_FONT)), y-CHANNEL_FONT, CHANNEL_FONT)
		drawLine(lineSrc.x, lineSrc.y, lineDest.x, lineDest.y, "black", CHANNEL_THICKNESS)

	def displayDimmSlot(self):
		print "Slot Number:%d"%self.slotNo
		print "Size:%d" %self.size

class Bus:
	def __init__(self,busId):
		self.busId = busId
		self.devices = {}
		self.isCalculated = False
		self.startPoint = Point(0, 0)
		self.endPoint = Point(0, 0)
		self.isActive = 0             #0->not calculated, -1->not active, 1->active
		self.marked = False           ## Whether bus is drawn or not
		#self.visited = False
		self.branchCount = 0      	  ## number of direct devices connected

	def displayBus(self):
		print "Bus Id:%d"%self.busId
		for devKey in self.devices.keys():
			self.devices.get(devKey).displayDevice()
		print "-------------------------------------"

class Device:
	def __init__(self,deviceId):
		self.deviceId = deviceId
		self.functions = {}
		
	def displayDevice(self):
		print "Device Id:%d"%self.deviceId
		for funcKey in self.functions.keys():
			self.functions.get(funcKey).displayFunction()
		print "-----------"

class Function:
	'This is Function class'
	def __init__(self, funcId, name, vendorId, deviceId, revisionId, deviceType, priBusNumber, secBusNumber, subBusNumber):
		self.funcId = funcId
		self.funcName = name
		self.vendorDeviceId = (vendorId<<16) + deviceId
		self.revisionId = revisionId
		self.deviceType = deviceType
		self.priBusNumber = priBusNumber
		self.secBusNumber = secBusNumber
		self.subBusNumber = subBusNumber
		self.startPoint = Point(0,0)
		self.nextBusPoint = 0             #Index of bus to be drawn
		self.isDimensionSet = False       # For bridges
		self.noOfActiveBridgeBuses = 0
		self.bridgeCount = 0
		self.busesOnSubBridge = 0
		if(deviceType == "Standard"):
			self.deviceLength = 1.0*DEVICE_LENGTH
			self.deviceBreadth = DEVICE_BREADTH
		else:
			self.deviceLength = 1.0*BRIDGE_LENGTH
			self.deviceBreadth = BRIDGE_BREADTH

                
	def setBridgeDimension(self, busId, parent):
		if( (self.isDimensionSet == True) ):
			return
		for subBusId in range(self.secBusNumber, (self.subBusNumber+1)):
			subBus = parent.buses.get(subBusId)
			if( (subBus != None) and (subBus.isActive == 1) and (subBus.marked == False) ):
				subBus.branchCount = getBusBranches(parent, subBus)
				self.noOfActiveBridgeBuses += subBus.branchCount
				subBus.marked = True
				for dev in subBus.devices.values():
					for func in dev.functions.values():
						if ( (func.deviceType == "Bridge") and (isActiveBridge(parent,func)) and (func.isDimensionSet==False) ):
							self.bridgeCount += 1
							func.setBridgeDimension(subBusId,parent)
							self.busesOnSubBridge += (func.deviceLength)/DISTANCE_BETWEEN_BUSES

		self.noOfActiveBridgeBuses = self.noOfActiveBridgeBuses- self.busesOnSubBridge+ (self.bridgeCount)
		self.deviceLength = (self.noOfActiveBridgeBuses) * DISTANCE_BETWEEN_BUSES
		self.isDimensionSet = True
		
	def displayFunction(self):
		print "Function Id:%d"%self.funcId
		print "Function Name:"+self.funcName
		print "VendorDeviceId:%d"%self.vendorDeviceId
		print "Device Type:"+self.deviceType
		if(self.secBusNumber != -1):
			print "Primary Bus Number:%d"%self.priBusNumber
			print "Secondary Bus Number:%d"%self.secBusNumber
			print "Subordinate Bus Number:%d"%self.subBusNumber

class PCH:
	'This is PCH class'
	def __init__(self):
		self.busNumbers = []
		self.activeBuses = 0.0
		self.startPoint = Point(0, 0)
		self.nextBusPoint = 0.0   #Index of bus to be drawn
		self.length = 2.0*DISTANCE_BETWEEN_BUSES ##Default length assuming PCH has 2 buses on average
		self.breadth = PCH_BREADTH ##Default breadth assuming socket has 3 dimm slots on average

	def setPCHDimension(self,sockt):
		newBuses = []
		for pchBusId in self.busNumbers:
			bus = sockt.buses.get(pchBusId)
			if( isActiveBus(sockt,bus) and (bus.marked == False) ):
				bus.branchCount = getBusBranches(sockt, bus)
				self.activeBuses += bus.branchCount
				newBuses.append(pchBusId)
				for dev in bus.devices.values():
					for func in dev.functions.values():
						if ( (func.deviceType == "Bridge") and (isActiveBridge(sockt,func)) ):
							func.setBridgeDimension(pchBusId, sockt)
							self.activeBuses += (func.deviceLength - DISTANCE_BETWEEN_BUSES)/DISTANCE_BETWEEN_BUSES
		self.busNumbers = newBuses 
		if( self.activeBuses == 0.0 ):   ##If no devices are active we just need to draw the PCH device
			self.activeBuses = 1.0
		print "PCH buses:%d"%self.activeBuses
		self.length = (self.activeBuses) * DISTANCE_BETWEEN_BUSES + SIZE_X/50.0

class Point:
	'This is point class'
	def __init__(self,x,y):
		self.x = x
		self.y = y

def getBusBranches(sockt,bus):
	count = 0
	if (bus == None):
		return 0
	if (bus.branchCount > 0):
		return bus.branchCount
	for dev in bus.devices.values():
		for func in dev.functions.values():
			if (func.deviceType == "Standard"):
				count += 1
			elif (isActiveBridge(sockt,func)):
				count += 1
	print "Bus %d has %d branches"%(bus.busId,count)
	return count
                                                                        
def isActiveBus(sockt,bus):##Just checks whether there is a standard device in the bus
	result = False
	if (bus == None):
		return False
	if( bus.isActive == 1):
		   return True
	for subdevice in bus.devices.values():
		for  subfunction in subdevice.functions.values():
			if (subfunction.deviceType == "Standard"):
				bus.isActive = 1
				print "bus %d is active"%bus.busId
				return True
			else:
				for subBus in range(subfunction.secBusNumber, (subfunction.subBusNumber+1)):
					result = result or isActiveBus(sockt, sockt.buses.get(subBus))
	if( result == False):
		print "bus %d is not active"%bus.busId
		bus.isActive = -1
	else:
		bus.isActive = 1
	return result

def isActiveBridge(sockt,bridge):
	result = False
	for subBus in range(bridge.secBusNumber, (bridge.subBusNumber+1)):
		if( (sockt.buses.get(subBus) != None) and (sockt.buses.get(subBus).isActive == 1)):
			return True
	return False

def parseXML(XmlFile):
	global pch, basePointy
	tree = ET.parse(XmlFile)
	platformDetails = tree.find("PLATFORM")
	platformName = platformDetails.attrib['NAME']
	pch = PCH()
	print "------------------------Parsing XML--------------------"
	sockets = tree.findall("Topology/Socket")
	for sockt in sockets:
		socketInfo = sockt.find("Socket")
		socketId = int(socketInfo.attrib['Id'])
		socketType = socketInfo.attrib['Type']
		socktObj = Socket(socketId, socketType, platformName)
		for node in sockt.getchildren():
			if ((node.tag == 'port') and (node.find('Link').attrib['Status'] != "OFF")):
				speed = node.find('Link').attrib['Speed']
				portNo = int(node.find('Port').attrib['Num'])
				peerSocket = int(node.find('PeerPortSocket').attrib['SocketId'])
				peerPort = int(node.find('PeerPortSocket').attrib['PeerPort'])
				portObj = Port(portNo, speed, peerSocket, peerPort)
				socktObj.ports.append(portObj)
		print "Added Socket: %d"%socketId
		socketDict[socketId] = socktObj
	if (len(socketDict) >= 4):
		basePointy = SIZE_Y/5
	#Parse Dimm Info
	sockets = tree.findall("DimmInfo/Socket")
	for  sockt in sockets:
		socketID = int(sockt.attrib['Id'],16)
		socktObj = socketDict.get(socketID)
		for controller in sockt.findall("Controller"):
			controllerObj = Controller(controller.attrib['Id'])
			for channel in controller.getchildren():
				channelNo = int(channel.attrib['Num'],16)
				channelObj = Channel(channelNo)
				for dimmSlot in channel.getchildren():
					dimmSize = int(dimmSlot.attrib['SizeMb'])
					if (dimmSize > 0):
						slotNo = int(dimmSlot.attrib['SlotNo'],16)
						vendorName = dimmSlot.attrib['Vendor']
						dimmObj = DimmSlot(slotNo, dimmSize, vendorName)
						channelObj.dimmSlots.append(dimmObj)
				controllerObj.channels.append(channelObj)
			socktObj.controllers.append(controllerObj)

	#Parse Package to get range of buses in sockets
	busesToBeIgnored = []
	packages = tree.findall("package")
	for package in packages:
		packageId = int(package.attrib['package-id'], 16)
		minBus = int(package.find("BusRange").attrib['min-bus'], 16)
		maxBus = int(package.find("BusRange").attrib['max-bus'], 16)
		socketDict.get(packageId).minBus = minBus
		socketDict.get(packageId).maxBus = maxBus
		if (minBus != 0):
			busesToBeIgnored.append(minBus)
		busesToBeIgnored.append(maxBus)

	#Parse PCI-Devices
	buses = tree.findall("pci-devices/Bus")
	for bus in buses:
		busId = int(bus.attrib['ID'], 16)
		if ( busId in busesToBeIgnored ):
			continue
		if (busId == 0):
			for device in bus.findall("Device"):
				deviceId = int(device.attrib['ID'], 16)
				if(deviceId == 28): ##For PCH buses
					for bridgeFunction in device.findall("Bridge-Function"):
						secBusNumber = int(bridgeFunction.find('SecondaryBusNumber').text, 16)
						subBusNumber = int(bridgeFunction.find('SubordinateBusNumber').text, 16)
						for busIndex in range(secBusNumber, (subBusNumber+1)):
							if(busIndex not in pch.busNumbers):
								pch.busNumbers.append(busIndex)
								print "Added PCH bus:%d"%busIndex
			continue

		b = Bus(busId)
		for device in bus.findall("Device"):
			deviceId = int(device.attrib['ID'], 16)
			if(deviceId):  # consider only DeviceId 0, to keep it simple
				continue
			d = Device(deviceId)
			for function in device.findall("Function"): #Standard Device
				funcId = int(function.attrib['ID'],16)
				vendorId = int(function.find('vendorID').text, 16)
				devId = int(function.find('deviceID').text, 16)
				revisionId = int(bridgeFunction.find('revisionID').text, 16)
				name = GetDevName(vendorId, devId, revisionId)
				f = Function(funcId, name, vendorId, devId, revisionId, "Standard", -1, -1, -1)
				d.functions[funcId] = f
				break

			for bridgeFunction in device.findall("Bridge-Function"): #Bridge
				funcId = int(bridgeFunction.attrib['ID'], 16)
				vendorId = int(bridgeFunction.find('vendorID').text, 16)
				devId = int(bridgeFunction.find('deviceID').text, 16)
				revisionId = int(bridgeFunction.find('revisionID').text, 16)
				priBusNumber = int(bridgeFunction.find('PrimaryBusNumber').text, 16)
				secBusNumber = int(bridgeFunction.find('SecondaryBusNumber').text, 16)
				subBusNumber = int(bridgeFunction.find('SubordinateBusNumber').text, 16)
				name = GetDevName(vendorId, devId, revisionId)
				f = Function(funcId, name, vendorId, devId, revisionId, "Bridge", priBusNumber, secBusNumber, subBusNumber)
				d.functions[funcId] = f
			b.devices[deviceId] = d
		addBusToSocket(busId, b)
	print "--------------------Parsed XML successfully----------------"
	return

def GetDevName(vendorId, deviceId, RevId):
	VenDevId = (deviceId<<16) + vendorId
	if( CardsDict.get(VenDevId) == None ):
		return "Unknown"
	if(VenDevId != 0x53758086):
		return CardsDict[VenDevId]
	else:
		if ((RevId & 0xF0) == 0x10):
			return "RUBICON"
		if ((RevId & 0xF0) == 0x20):
			return "LAGUNA"
		return "CORIN"

def addBusToSocket(busId, bus):
	for sockt in socketDict.values():
		if( busId in range(sockt.minBus, sockt.maxBus) ):
			sockt.buses[busId] = bus
			print "Added Bus %d to Socket %d"%(busId, sockt.socketId)
			break

def drawBus(parentSocket, parent, bus, parentType, length, breadth, drawingDirection):    #Parent is either socket or Bridge

	baseX = parent.startPoint.x
	baseY = parent.startPoint.y
	d = DISTANCE_BETWEEN_BUSES

	bus.isCalculated = True
	print "Drawing bus:%d at point %f" %(bus.busId, parent.nextBusPoint)
	busesDrawn = 0
	if ( (parentType == "Socket") or (parentType == "Bridge") or (parentType == "PCH") ):
		x1 = baseX + (d*parent.nextBusPoint ) + (SIZE_X/100.0)
		x2 = x1
		sign = 1
		if ( drawingDirection == "DRAW_ABOVE" ):
			y1 = baseY
			y2 = baseY + BUS_LENGTH
		else:
			y1 = baseY - breadth
			y2 = baseY - BUS_LENGTH - breadth
			sign = -1

		drawLine(x1, y1, x2, y2, "black", BUS_THICKNESS)
		
		
		branchCount = bus.branchCount
		print "Bus %d drawing with branches %d"%(bus.busId,branchCount)
		if (branchCount > 1):
			y1 = y1 + ((y2-y1)/2)
			drawLine(x1, y1, x2 + d*(branchCount-1), y1, "black", BUS_THICKNESS)
		count = 0
		for subdevice in bus.devices.values():
			for subfunction in subdevice.functions.values():
				p = x2 + (count * d)
				q = y2
				if( subfunction.deviceType == "Standard" ):
					startX = p-(DEVICE_LENGTH/2)
					if( sign == 1 ):
						startY = q + DEVICE_BREADTH
						lengthDifference = NO_OF_CHARACTERS_OF_FUNCTION - len(subfunction.funcName)
						if( lengthDifference <= 1 ):
							drawText(None, subfunction.funcName, startX, startY, FUNC_NAME_FONT)
						else:
							drawText(None, subfunction.funcName, startX+(lengthDifference*(FUNC_NAME_FONT/2)), startY, FUNC_NAME_FONT)
					else:
						startY = q
						lengthDifference = NO_OF_CHARACTERS_OF_FUNCTION - len(subfunction.funcName)
						if( lengthDifference <= 1 ):
							drawText(None, subfunction.funcName, startX, (startY - DEVICE_BREADTH - (FUNC_NAME_FONT*2)), FUNC_NAME_FONT)
						else:
							drawText(None, subfunction.funcName, (startX + (lengthDifference*(FUNC_NAME_FONT/2))), (startY - DEVICE_BREADTH - (FUNC_NAME_FONT*2)), FUNC_NAME_FONT)
					subfunction.startPoint = Point(startX, startY)
					drawRectangle(DEVICE_LENGTH, DEVICE_BREADTH, startX, startY, "Dev", DEVICE_FONT, DEVICE_COLOR, "italic", DEVICE_THICKNESS)
					drawLine(p, y1, p, q, "black", BUS_THICKNESS)
					count += 1
				else: ##If its a bridge
					if ( parentType == "PCH" ): ##If it is PCH bridge
						parent = socketDict.get(0)
					if ( isActiveBridge(parentSocket, subfunction) ):
						subfunction.setBridgeDimension(bus.busId, parentSocket)
						count += 1
						drawLine(p, y1, p, q, "black", BUS_THICKNESS)
						busesDrawn = subfunction.deviceLength/DISTANCE_BETWEEN_BUSES
						subfunction.startPoint = Point( (p-(subfunction.deviceLength/2)), (q+BRIDGE_BREADTH) )
						drawRectangle(subfunction.deviceLength, subfunction.deviceBreadth, subfunction.startPoint.x, subfunction.startPoint.y, "Brg", BRIDGE_FONT, BRIDGE_COLOR, "bold", DEVICE_THICKNESS)
						for subBus in range(subfunction.secBusNumber, (subfunction.subBusNumber+1)):
							if( (parentSocket.buses.get(subBus) != None) and (parentSocket.buses.get(subBus).isActive == 1) and (parentSocket.buses.get(subBus).isCalculated == False)): 
									drawBus(parentSocket, subfunction, parentSocket.buses.get(subBus), "Bridge", subfunction.deviceLength, subfunction.deviceBreadth, drawingDirection)
				
				if ( parentType == "PCH" ):
					pch.nextBusPoint = pch.nextBusPoint + max(branchCount, busesDrawn)
				else:
					parent.nextBusPoint = parent.nextBusPoint + branchCount 
	return

def DrawCpuSubSystem(SktNo):
	global pch
	#draw socket
	sockt = socketDict.get(SktNo)
	sockt.drawSocket()
	# draw dimms
	for controller in sockt.controllers:
		for channel in controller.channels:
			for dimmSlot in channel.dimmSlots:
				dimmSlot.setChannelPoint(sockt, controller, channel)
				dimmSlot.draw_channel(sockt, controller, channel)
	# draw PCH
	if(SktNo == 0):
		drawPCH()
		for pchBusId in pch.busNumbers:
			bus = sockt.buses.get(pchBusId)
			if(bus.isCalculated == False):
				drawBus(sockt, pch, bus, "PCH", pch.length, pch.breadth, "DRAW_ABOVE")
	# draw devices and bridges
	if ( SktNo < 2 ):
		for bus in sockt.buses.values():
			if( (isActiveBus(sockt,bus)) and (bus.isCalculated == False) ):
				drawBus(sockt, sockt, bus, "Socket", sockt.socketLength, sockt.socketBreadth, "DRAW_ABOVE")
	else:
		for bus in sockt.buses.values():
			if( (isActiveBus(sockt,bus)) and (bus.isCalculated == False) ):
				drawBus(sockt, sockt, bus, "Socket", sockt.socketLength, sockt.socketBreadth, "DRAW_BELOW")

def drawGUI():
	max_length = max_breadth = 0.0
	for sockt in socketDict.values():
		sockt.setActiveBusesCount()
		sockt.setSocketDimension()
		if ( sockt.socketLength > max_length ):
			max_length = sockt.socketLength
		if ( sockt.socketBreadth > max_breadth ):
			max_breadth = sockt.socketBreadth

	for sockt in socketDict.values():
		sockt.socketLength = max_length
		sockt.socketBreadth = max_breadth                    

	max_length = 0.0
	for sockt in socketDict.values():
		busCount = 0
		if ( sockt.socketId == 0 ):
			pch.setPCHDimension(sockt)
			busCount += pch.activeBuses
		for bus in sockt.buses.values():
			bus.branchCount = getBusBranches(sockt,bus)
			if( (bus.busId not in pch.busNumbers) and (isActiveBus(sockt,bus)) and (bus.marked==False)):
				for dev in bus.devices.values():
					for func in dev.functions.values():
						if ( (func.deviceType == "Bridge") and (isActiveBridge(sockt,func)) ):
							func.setBridgeDimension(bus.busId, sockt)
							sockt.noOfBridgeBuses = sockt.noOfBridgeBuses + (func.deviceLength/DISTANCE_BETWEEN_BUSES)
						elif (isActiveBus(sockt,bus)):
							busCount += bus.branchCount
		print "No. of active buses %d,%d" %(busCount,sockt.noOfBridgeBuses)
		busCount = busCount + sockt.noOfBridgeBuses
		sockt.socketLength = max(0.75*pch.length, (busCount-1.0)*(DISTANCE_BETWEEN_BUSES ))+ (SIZE_X/50.0)
		if ( sockt.socketLength > max_length ):
			max_length = sockt.socketLength
	for sockt in socketDict.values():
		sockt.socketLength = max_length
		sockt.setSocketStartPoint()
	##Start drawing the objects
	print "-------------------Drawing GUI------------------------"
	drawText(None, ("Platform Name: "+socketDict.get(0).platformName), -SIZE_X/5, (SIZE_Y*0.45), DISPLAY_BIOS_INFO_FONT)
	for sockt in socketDict.values():
		print "Drawing Socket:%d"%sockt.socketId
		DrawCpuSubSystem(sockt.socketId)
	print "Completed drawing all sockets..."

	##Calculate QPI links
	for sockt in socketDict.values():
		for port in sockt.ports:
			if( port.isCalculated == False ):
				port.setPortPoint(sockt)
				port.isCalculated = True
	##Draw QPI links
	print "Drawing QPI links"
	for sockt in socketDict.values():
		for port in sockt.ports:
			if( port.isDrawn == False ):
				port.draw_portConnection(sockt)
				port.isDrawn = True

	print "---------------Completed GUI drawing------------------"
	window.onclick(displayFunc)

	##Hide all turtles on screen
	for turtl in window.turtles():
		turtl.hideturtle()

def displayFunc(x,y):
	global textData
	global INFO_FLAG
	if ( INFO_FLAG == False ):
		for sockt in socketDict.values():
			for controller in sockt.controllers:
				for channel in controller.channels:
					for dimmSlot in channel.dimmSlots: 
						if ( isWithinBoundary(x, y, dimmSlot.channelPoint, DIMM_LENGTH, DIMM_BREADTH) ):
							textData.append("Vendor: " + str(dimmSlot.vendorName))
							textData.append("Size: " + str(dimmSlot.size) + "Mb")
							drawDialogueBox(printTurtle, x, y, DIMM_INFO_FONT, "maroon")
							INFO_FLAG = True
							return
			for bus in sockt.buses.values():
				for device in bus.devices.values():
					for function in device.functions.values():
						if ( (function.deviceType == "Standard") and (isWithinBoundary(x, y, function.startPoint, DEVICE_LENGTH,DEVICE_BREADTH)) ):
							textData.append("%s" %GetDevName((function.vendorDeviceId>>16) & 0xFFFF, (function.vendorDeviceId & 0xFFFF), function.revisionId))
							textData.append("VenDevId: 0x%X" %function.vendorDeviceId)
							textData.append("B=0x%X; D=0x%X; F=0x%X" %(bus.busId, device.deviceId, function.funcId))
							drawDialogueBox(printTurtle, x, y, DEVICE_INFO_FONT, "green")
							INFO_FLAG = True
							return
						elif( (function.deviceType == "Bridge") and (isWithinBoundary(x, y, function.startPoint, function.deviceLength, function.deviceBreadth) ) ):
							textData.append("%s" %GetDevName((function.vendorDeviceId>>16) & 0xFFFF, (function.vendorDeviceId & 0xFFFF), function.revisionId))
							textData.append("VenDevId: 0x%X" %function.vendorDeviceId)
							textData.append("B=0x%X; D=0x%X; F=0x%X" %(bus.busId, device.deviceId, function.funcId))
							drawDialogueBox(printTurtle, x, y, BRIDGE_INFO_FONT, "green")
							INFO_FLAG = True                        
	else:
		printTurtle.clear()
		INFO_FLAG = False
		textData = []

def getMaxLineLength(textData):
	maxLen = 0
	for line in textData:
		if ( len(line) > maxLen ):
			maxLen = len(line)
	return maxLen

def drawDialogueBox(turtl,x,y,fontSize,color):
	global textData
	noOfLines = len(textData)
	length = (0.67*getMaxLineLength(textData)*fontSize) + (2*fontSize)
	breadth = noOfLines*(2*fontSize)
	turtl.pensize(3)
	turtl.penup()
	turtl.goto(x-10, y+10)
	turtl.pendown()

	turtl.fillcolor(color)
	turtl.fill(True)
	turtl.begin_poly()
	turtl.goto(x, y)
	turtl.goto(x+10, y+10)
	turtl.goto(x+(0.67*length), y+10)
	turtl.goto(x+(0.67*length), (y+10+breadth))
	turtl.goto(x-(length/3), (y+10+breadth))
	turtl.goto(x-(length/3), y+10)
	turtl.goto(x-10, y+10)
	turtl.end_poly()
	turtl.fill(False)
	turtl.color("black")
	i = 0
	for line in textData:
		drawText(turtl , line , x-(length/3)+fontSize , y+breadth-(i*(fontSize*2))-fontSize , fontSize)
		i += 1

def isWithinBoundary(x,y,startPoint,length,breadth):
	if ( ((x >= startPoint.x) and (x <= (startPoint.x+length))) and ((y >= startPoint.y-breadth) and (y <= startPoint.y)) ):
		return True
	return False

def drawPCH(): ##Draw PCH block on socket
	baseX = socketDict.get(0).startPoint.x
	baseY = socketDict.get(0).startPoint.y
	x1 = baseX + DISTANCE_BETWEEN_BUSES*(socketDict.get(0).nextBusPoint) + SIZE_X/100
	x2 = x1
	y1 = baseY
	y2 = baseY + BUS_LENGTH    
	socketDict.get(0).nextBusPoint +=  pch.activeBuses
	drawLine(x1, y1, x2, y2, "black", BUS_THICKNESS)
	pch.startPoint=Point(x2-(pch.length/2), y2+pch.breadth)
	drawRectangle(pch.length, pch.breadth, pch.startPoint.x, pch.startPoint.y, "PCH", PCH_FONT, PCH_COLOR, "bold", PCH_THICKNESS)

def drawRectangle(length, breadth, x, y, txt, fontSize, color, fontType, thickness):
	t = turtle.Turtle()
	t.speed(0)
	if ( (color == None) or (color == "") ):
		color = "black"
	t.penup()
	t.setposition(x, y)
	t.pendown()

	t.pensize(thickness)
	t.fillcolor(color)
	t.fill(True)
	t.begin_poly()
	t.goto(x+length, y)
	t.goto(x+length, y-breadth)
	t.goto(x, y-breadth)
	t.goto(x, y)
	t.end_poly()
	t.fill(False)

	t.penup()
	t.setposition((x+(length/2)-(len(txt)*0.4*fontSize)), (y-(breadth/2)-(0.834*fontSize)))
	t.color("black")
	t.write(txt, True, font=("Arial", fontSize, fontType))
	t.hideturtle()

def drawText(textTurtle,string,x,y,fontSize):
	if( textTurtle == None ):
		textTurtle = turtle.Turtle()
	textTurtle.speed(0)
	textTurtle.penup()
	textTurtle.setposition(x, y)
	textTurtle.pendown()
	textTurtle.write(string, font=("Arial", fontSize, "normal"))
	textTurtle.hideturtle()

def drawLine(x1, y1, x2, y2, color, thickness):
	lineTurtle = turtle.Turtle()
	lineTurtle.speed(0)
	if( (color == None) or (color == "") ):
		color = "black"
	if( (thickness != None) or (thickness != 0) ):
		lineTurtle.pensize(thickness)
	lineTurtle.color(color)
	lineTurtle.penup()
	lineTurtle.setposition(x1, y1)
	lineTurtle.pendown()
	lineTurtle.setposition(x2, y2)
	lineTurtle.hideturtle()

def DrawSchema(XmlFile=0):        
	if(XmlFile == 0):
		import os, sys
		sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
		import XmlCliLib as lib
		lib.SaveXml()
		XmlFile = lib.PlatformConfigXml
	initializeScreen()
	for turtl in window.turtles():
		turtl.clear()
	parseXML(XmlFile)
	drawGUI()
	turtle.done()

def DrawAll(XmlPath):
	for XmlFile in glob.iglob(XmlPath + "/*.xml"):
		DrawSchema(XmlFile)

def main():
	Operation = sys.argv[1].lower()
	if (Operation == "drawall"):
		DrawAll(sys.argv[2])
	if (Operation == "draw"):
		DrawSchema(sys.argv[2])

if __name__ == '__main__':
	main()
