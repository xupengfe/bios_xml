#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types

########### Code to run @ import time ##############

class stubAccess(_cliutil.cliaccess):
	def __init__(self):
		super(stubAccess,self).__init__("stub")

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		return 0

	def CloseInterface(self):
		return 0

	def warmreset(self):
		return 0

	def coldreset(self):
		return 0

	def memBlock(self, address, size):
		return 0

	def memsave(self, filename, address, size):
		return 0

	def memread(self, address, size):
		return 0

	def memwrite(self, address, size, value):
		return 0

	def load_data(self, filename, address):
		return 0

	def readIO(self, address, size):
		return 0

	def writeIO(self, address, size, value):
		return 0

	def triggerSMI(self, SmiVal):
		return 0

	def ReadMSR(self, Ap, MSR_Addr):
		return 0

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return 0

	def ReadSmbase(self):
		return 0
