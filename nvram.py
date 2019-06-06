#!/usr/bin/env python2.7
############################################################################
# INTEL CONFIDENTIAL
# Copyright 2005 2006 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related
# to the source code ("Material") are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel Corp-
# oration or its suppliers and licensors. The Material may contain trade
# secrets and proprietary and confidential information of Intel Corpor-
# ation and its suppliers and licensors, and is protected by worldwide
# copyright and trade secret laws and treaty provisions. No part of the
# Material may be used, copied, reproduced, modified, published, uploaded,
# posted, transmitted, distributed, or disclosed in any way without
# Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellect-
# ual property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property
# rights must be express and approved by Intel in writing.
############################################################################

import types as _types
import os as _os
import sys as _sys
import binascii as _binascii
import time as _time
import copy as _copy
import weakref as _weakref

try:
	import xml.etree.cElementTree as ET
except:
	import xml.etree.ElementTree as ET

_sys.path.append(_os.path.abspath(_os.path.dirname(__file__)))

import XmlCliLib as _clb

import tools.toolbox as _tools
import tools.parsingUtil as _pu

_log = _tools.getLogger("nvram")
_log.setFile("nvram.log",dynamic=True)
_log.setFileFormat("simple")
_log.setFileLevel("info")
_log.setConsoleLevel("result")

_debug=False
_known_modes = ['gbt','gbt2']

_recommendedaccess = "gbt"
	
def getNVRAM(file=None, type=None):
	global _recommendedaccess
	if type == None:
		type = _recommendedaccess
	
	assert type in _known_modes, "Invalid NVRAM Acesss method '%s' (valid:gbt/epcs)"%type
	
	if type == "gbt":
		return gbtNVRAM(file=file)
	
	assert False, "Invalid input (type:'%s' & file='%s')"%(type,file)
	
_gbtComandSubType = ["Append", "RestoreModify", "ReadOnly", "LoadDefaults"]
_gbtComandSubTypeDict = {"Append":0x0, "RestoreModify":0x1, "ReadOnly":0x2, "LoadDefaults":0x3}
_gbtComandSideEffect = ["NoSideEffect", "WarmResetRequired", "PowerGoodResetRequired", "Reserved"]
_SideEffectVal = 0
_CpuSvFlexconFlow = False

class KnobSelection():
	def __init__(self, value, name):
		self.value=_pu.str2long(value)
		self.name=name
	def __repr__(self):
		return "<%s 0x%X = \"%s\">"%(self.__class__.__name__,self.value,self.name)

class KnobSelectionMap():
	def __init__(self,*args):
		self.__dict__["_map"]=list(*args)
		self.__dict__["depex"] = []
	def _getByValue(self,value):
		return filter(lambda x: x.value == value,self._map)
	def _getByName(self,name):
		return filter(lambda x: x.name == name,self._map)
	def _addSelection(self, value,name):
		self._map.append(KnobSelection(value,name))
	def hasValue(self,value):
		return len(self._getByValue(value)) > 0
	def hasName(self,name):
		return len(self._getByName(name)) > 0
	def name2value(self,name):
		return map(lambda x: x.value, self._getByName(name))
	def value2name(self,value):
		return map(lambda x: x.name, self._getByValue(value))
	def getList(self):
		return self._map
	def getValues(self):
		return map(lambda x: x.value,self._map)
	def getNames(self):
		return map(lambda x: x.name, self._map)
	def __getitem__(self, key):
		return self._map[key]
	def __setitem__(self,key,value):
		self._map[key]=value
	def __len__(self):
		return len(self._map)
	def __repr__(self):
		#return "["+"\n".join(map(str,self._map))+"]"
		return "["+",".join(map(str,self._map))+"]"
	
class KnobValue():
	def __init__(self, initial=None, default=None, current = None):
		self.__dict__["_initial"] = initial
		self.__dict__["_default"] = default
		if current != None:
			self.__dict__["_current"] = current
		else:
			self.__dict__["_current"] = initial
		self._touched = False
	
	def __eq__(self,other):
		if isinstance(other, KnobValue):
			return self.getCurrent() == other.getCurrent()
		elif _pu.isNumber(other):
			return self.getCurrent() == other
		else:
			assert False, "Invalid KnobValue Comparison. (type:%s)"%str(type(other))
			
	def __ne__(self,other):
		return (self.getCurrent() != other)
	
	def __gt__(self,other):
		return (self.getCurrent() > other)
	
	def __ge__(self,other):
		return (self.getCurrent() >= other)
	
	def __lt__(self,other):
		return (self.getCurrent() < other)
		
	def __le__(self,other):
		return (self.getCurrent() <= other)
	
	def _update(self,other,setInitial=False,setDefault=False):
		assert isinstance(other,KnobValue), "KnobValue._update requires a KnobValue object as the input parameter"
		self.setCurrent(other.getCurrent())
		if setInitial:
			self._setInitial(other.getInitial())
		if setDefault:
			self._setDefault(other.getDefault())
	
	def isDirty(self, delta=False):
		if delta:
			return self.getInitial() != self.getCurrent()
		else:
			return self._touched
	
	def clearDirty(self):
		self._setInitial(self.getCurrent())
		self._touched=False
		
	def getInitial(self):
		return self._initial
	
	def _setInitial(self,value):
		assert _pu.isNumber(value), "KnobValue._setInitial requires a number %s (type:%s)"%(value,type(value))
		self._initial=value
		
	def getDefault(self):
		return self._default
		
	def _setDefault(self,value):
		assert _pu.isNumber(value), "KnobValue._setDefault requires a number %s (type:%s)"%(value,type(value))
		self._default=value
		
	def getCurrent(self):
		return self._current
		
	def setCurrent(self,value):
		assert _pu.isNumber(value), "KnobValue.setCurrent requires a number %s (type:%s)"%(value,type(value))
		self._touched=True
		self._current=value

class KnobAddressVIO():
	def __init__(self, varstoreIndex=0xFF,offset=0,size=0):
		self.__dict__["varstoreIndex"] = varstoreIndex
		self.__dict__["offset"] = offset
		self.__dict__["size"] = size
	def __eq__(self,other):
		if isinstance(other, self.__class__):
			return (self.offset == other.offset and self.varstoreIndex == other.varstoreIndex) # self.size == other.size
		elif isinstance(other, _types.TupleType) and len(other) == 2:
			return (self.varstoreIndex,self.offset) == other
		else:
			return False
	def __ne__(self,other):
		return not self.__eq__(other)
	def __hash__(self):
		return self.varstoreIndex << 16 | self.offset
		#return hash((self.varstoreIndex, self.offset))
	def __repr__(self):
		return "<%s \"varstoreIndex\"=0x%x & \"offset\"=0x%02x>"%(self.__class__.__name__,self.varstoreIndex,self.offset)
		
class KnobDefinition():
	def __init__(self, kValue=None):
		self.__dict__["setupType"]=""
		self.__dict__["selections"]=KnobSelectionMap()
		self.__dict__["name"]=""
		self.__dict__["owner"]=""				# Used for flexcon
		self.__dict__["description"]=""
		self.__dict__["_value"] = kValue
		self.__dict__["path"] = ""
		self.__dict__["severity"] = "DISABLED"	# Used for KnobDefinition Checking
#		self.__dict__["varstoreIndex"]=None
#		self.__dict__["offset"]=None
#		self.__dict__["size"]=None
		self.__dict__["_address"] = None
		self.__dict__["prompt"]=None
		self.__dict__["depex"]=None
		self.__dict__["type"]=None
		
	def __eq__(self, other):
		if isinstance(other, self.__class__):
			return (self.name == other.name and self.getValue() == other.getValue())
		if _pu.isNumber(other):
			return self.getValue() == other
		elif self.setupType == "numeric" and isinstance(other, _types.StringType):
			return self.getValue() == _pu.str2long(other)
		else:
			matchlist = self.getString()
			if other in matchlist:
				return True
			elif other in ["Enabled","Enable","Disable","Disabled"]:
				if other == "Enable":
					return "Enabled" in matchlist
				elif other == "Enabled":
					return "Enable" in matchlist
				elif other == "Disable":
					return "Disabled" in matchlist
				elif other == "Disabled":
					return "Disable" in matchlist
			else:
				return False
	
	def __ne__(self,other):
		return not self.__eq__(other)

	def __gt__(self,other):
		return (self.getValue() > other)
	
	def __ge__(self,other):
		return (self.getValue() >= other)
	
	def __lt__(self,other):
		return (self.getValue() < other)
		
	def __le__(self,other):
		return (self.getValue() <= other)
		
	def __setattr__(self, attribute, value):
		if not attribute in self.__dict__:
			print "Cannot set %s" % attribute
		else:
			self.__dict__[attribute] = value
	
	def __hash__(self):
		return hash(self.getAddress())
		#return hash((self.varstoreIndex, self.offset))

	
	def __repr__(self):
#		if self._value == None or self._value.current == None:
#			value = "\"**Uninitialized**\""
#		else:
		error=False
		try:
			tmpMatch = self.getString()
		except:
			value = "**MissingValue**"
			error=True
		else:
			if len(tmpMatch) == 0:
				value = "**Invalid** (0x%X)"%self.getValue()
			else:
				value = tmpMatch[0]
		if self.setupType in ["oneof","checkbox"] and not error:
			return "<%s \"%s\" = \"%s\">"%(self.__class__.__name__,self.name,value)
		else:
			return "<%s \"%s\" = %s>"%(self.__class__.__name__,self.name,value)
	
	def isValidString(self,name):
		if self.setupType in ["oneof","checkbox"]:
			if name == "Enabled" and not self.selections.hasName(name) and self.selections.hasName("Enable"):
				name = "Enable"
			elif name == "Enable" and not self.selections.hasName(name) and self.selections.hasName("Enabled"):
				name = "Enabled"
			elif name == "Disabled" and not self.selections.hasName(name) and self.selections.hasName("Disable"):
				name = "Disable"
			elif name == "Disable" and not self.selections.hasName(name) and self.selections.hasName("Disabled"):
				name = "Disabled"
			return self.selections.hasName(name)
#		elif self.setupType in ["numeric"]:
		else:
			try:
				return self.isValidValue(_pu.str2long(name,16))
			except:
				_log.debug("Caught an exception when running isValidString on NUMERIC selection of '%s' with selection list of %s"%(name,self.selections))
				return False
#		else:
#			assert False, "You should not be here! fn:isValidSelection()"
	
	def getAddress(self):
		return self._address
		
	def _setAddress(self, adr):
		self._address = adr
	
	def isValidValue(self,value):
		if self.setupType == "oneof":
			return self.selections.hasValue(value)
		elif self.setupType == "checkbox":
			return self.selections.hasValue(value)
		#elif self.setupType == "numeric":
		else:
			assert _pu.isNumber(value), "isValidValue only accepts numbers" 
			# Try to find a valid selection.
			ret = True
			if self.selections.hasName("Minimum"):
				ret &= (value >= self.selections.name2value("Minimum")[0])
			if self.selections.hasName("Maximum"):
				ret &= (value <= self.selections.name2value("Maximum")[0])
			return ret
	
	def getString(self,index=None):
		if self.getValue() == None:
			ret = list()
		if self.setupType in ["checkbox","oneof"]:
			if self.selections.hasValue(self.getValue()):
				ret = self.selections.value2name(self.getValue())
			else:
				ret = list()
		else:
			ret = ["0x%X"%self.getValue()]
			
		if index == None:
			return ret
		else:
			assert len(ret) > index, "%s.getString() requested index %i, but only %i entries exist!"%(self.__class__.__name__,index,len(ret))
			return ret[index]
	
	def getValue(self):
		assert self._value != None, "%s is not associated with a KnobValue object yet. Sorry!"%(self.__class__.__name__)
		return self._value.getCurrent()
	
	def set(self,value):
		if _pu.isNumber(value) or self.setupType == "numeric":
			self.setValue(_pu.str2long(value))
		elif isinstance(value,(_types.StringType,_types.UnicodeType)):
			self.setString(value)
		else:
			assert False, "Invalid parameter type passed into %s.set() (obj: %s / type:%s)"%(self.__class__.__name__,value,type(value))
	
	def setString(self,name):
		if self.setupType in ["checkbox","oneof"]:
			if not self.selections.hasName(name):
				if name == "Enabled" and self.selections.hasName("Enable"):
					name = "Enable"
				elif name == "Enable" and self.selections.hasName("Enabled"):
					name = "Enabled"
				elif name == "Disabled" and self.selections.hasName("Disable"):
					name = "Disable"
				elif name == "Disable" and self.selections.hasName("Disabled"):
					name = "Disabled"
			assert self.selections.hasName(name),"setString could not find specified name (knob.name:\"%s\" & setString.name:\"%s\")"%(self.name,name)
			self.setValue(self.selections.name2value(name)[0])
		else:
			self.setValue(_pu.str2long(name))
			
	def setValue(self,value):
		assert _pu.isNumber(value), "setValue only accepts numbers"
		#assert self.setupType in ["numeric"] or self.selections.hasValue(value),"setValue could not find valid key for knob \"%s\" for value (%x)"%(self.name,value)
		assert self._value != None, "%s is not associated with a KnobValue object yet. Sorry!"%(self.__class__.__name__)
		self._value.setCurrent(value)
		
	def _isDirty(self, delta=False):
		assert self._value != None, "%s is not associated with a KnobValue object yet. Sorry!"%(self.__class__.__name__)
		return self._value.isDirty(delta=delta)
		
class NVRAM(object):
	def __init__(self):
		self.__dict__["_names"] = []
		self.__dict__["_knobs"]={}
		self.__dict__["_valueMap"] = {}
		self.__dict__["_version"] = None
		self.__dict__["_broken"]=[]
	
	def __getitem__(self, key):
		return self._knobs[self.getNames()[key]]
	
	def __len__(self):
		return len(self.getNames())
		
	def __getattr__(self,attr):
		# turns out this check is pretty fast, checking list instead of dict...may use list for what is "present"
		"""attribute was missing, see if it was in regdict"""
		if attr in self.getNames(): # turns out this check is pretty fast
			return self._knobs[attr]
		else:
			raise AttributeError("missing attribute %s"%attr)

	def __dir__(self):
		myattrs = self.__dict__.keys() + self.__class__.__dict__.keys() 
		myattrs.extend( self._names )
		return myattrs
	
	def __setattr__(self, name, value):
		"""Check to see if the attribute is Register class before handling"""
		if name in self.__dict__:
			self.__dict__[name] = value
		elif name in self._names:
			self._knobs[name].set(value) 
#		elif self.__dict__.has_key(name):
#			self.__dict__[name] = value
		else:
			raise AttributeError("Unknown attribute: %s, and this object does not allow dynamic adds"%name)
	
	def getNames(self):
		return self._names
		
	def getID(self):
		biosID = _clb.getBiosDetails()[1]
		return biosID
	
	def clone(self):
		newone = self.__class__()
		newone._valueMap=_copy.deepcopy(self._valueMap)
		newone._names =_copy.deepcopy(self._names)
		for knobName,knobDef in self._knobs.items():
				newKnob = _copy.copy(knobDef)
				newKnob._value = _weakref.proxy(newone._valueMap[hash(newKnob)])
				newone._knobs[knobName]=newKnob
		return newone
	
		
	def getVersion(self):
		return self._version
		
	def existName(self,name):
		return name in self._names
		
	def existAddress(self, index, offset):
		#return len(list(x.name for x in self._knobs.values() if x.getAddress() == (index, offset))) > 0
		return (index << 16 | offset) in self._valueMap
	
	def searchNames(self,name,exact=False):
		assert isinstance(name,(_types.StringType,_types.UnicodeType)),"searchNames only works on strings. Type = %s"%type(name)
		if exact:
			return list(str(x.name) for x in self._knobs.values() if name.lower() == x.name.lower())
		else:
			return list(x.name for x in self._knobs.values() if name.lower() in x.name.lower())
		
	def searchOwners(self,owner):
		assert isinstance(owner,_types.StringType),"searchforKnobByOwner only works on strings. Type = %s"%type(val)
		return list(x.name for x in self._knobs.values() if x.owner.lower() == owner.lower())
	
	def getByName(self,name):
		assert isinstance(name,(_types.StringType,_types.UnicodeType)),"getByName only works on strings. Type = %s"%type(name)
		return self._knobs[name]
	
	def getByAddress(self, index, offset):
		tmp=list(x for x in self._knobs.values() if x.getAddress() == (index, offset))
		assert len(tmp) != 1,"getByAddress found %i knobs with matched VarStoreIndex (0x%x) and Offset (0x%x)."%(len(tmp),index, offset)
		return (tmp[0])
	
	def setByName(self,name,value):
		self.getByName(name).set(value)
		
	def clearcmos(self):
		#Wiping CMOS
		_clb.clearcmos()
		self._clearNVdata()
	
	def _clearNVdata(self):
		#Flushing NVRAM data structures
		self._knobs={}
		self._valueMap = {}
		self._broken=[]
		self._names=[]
		self._version=None
	
	def _addKnob(self,kDef,kValue):
		if _debug:
			# Check that setupType is valid
			if kDef.setupType not in ['numeric','checkbox',"oneof","readonly"]:
				_log.result("\001ired\001Error: Invalid NVRAM type specified: \"%s\""%kDef.setupType)
				self._broken.append(kDef)
				return 1
			
			# If checkbox, confirm valid selectin options exist ("Checked" "Unchecked")
			if kDef.setupType == "checkbox":
				if not reduce(lambda y,z: y and z,map(lambda x: x in ["Checked","Unchecked"],kDef.selections.getNames()), True):
					_log.result("\001ired\001Error: BiosOption of setupType \"checkbox\" can only contain two options:\"Checked\" and \"Unchecked\". You passed in [%s]"%",".join(kDef.selections.getValues()))
					self._broken.append(kDef)
					return 1
			
			if not kDef.isValidValue(kValue.getCurrent()):
				_log.result("\001ired\001Error: The Bios Option \"%s\" current value doesn't map into the knob's selections"%kDef.name)
				self._broken.append(kDef)
				return 1
			
			# Confirm that selections is a dictionary
			if not isinstance(kDef.selections,KnobSelectionMap):
				_log.result("\001ired\001Error: Problem parsing the KnobDefinition. Incorrect type expected for BiosOption selections. Must be of type KnobSelectionMap")
				self._broken.append(kDef)
				return 1
			
			# Do type conversion just in case...
			for item in kDef.selections.getList():
				item.value = _pu.str2long(item.value)
				item.name = str(item.name)
				
			# Check that knob description is a String
			if not isinstance(kDef.description,_types.StringType):
				_log.result("\001ired\001Error: BiosOption description must be a String Type (%s)"%type(kDef.description))
				self._broken.append(kDef)
				return 1
			
			#check taht knob owner is a String
			if not isinstance(kDef.owner,(_types.StringType,_types.UnicodeType)):
				_log.result("\001ired\001Error: BiosOption owner must be a String Type (%s)"%type(kDef.owner))
				self._broken.append(kDef)
				return 1
			
			#If kDef.name is empty/None, then use formated version of description
			if kDef.name == None:
				kDef.name=kDef.description.lower().replace(" ","")
			
			if kValue.getCurrent() == None:
				kValue.setCurrent(kValue.getInitial())
			
			# Check for pre-existing Knob
		uniquename = not self.existName(kDef.name)
		uniqueaddress = not self.existAddress(kDef.getAddress().varstoreIndex, kDef.getAddress().offset)
#		else:
#			uniquename = True
#			uniqueaddress = True
		if uniqueaddress and uniquename:
			self._valueMap[hash(kDef)] = kValue
			kDef._value = _weakref.proxy(kValue)
			self._knobs[kDef.name]=kDef
			self._names.append(kDef.name)
		elif uniqueaddress and not uniquename:
			# Same name as existing knob but offsets differ
			tmpK = self.getByName(kDef.name)
			_log.error("\001ired\001Error: Cannot add knob with pre-existing name and new offset. (kDef.name=\"%s\" & new.offset=\"%s\" & old.offset=\"%s\")"%(kDef.name,kDef.offset,tmpK.offset))
			self._broken.append(kDef)
			return 1
		else:	#non-unique address
			if not uniquename:
				addrmatch=self.getByAddress(kDef.getAddress().varstoreIndex,kDef.getAddress().offset)
				if kDef.depex == addrmatch.depex:
					_log.warning("\i001iyellow\001Warning: New knob matches existing knob name (\"%s\"), address (%s), AND depex (\"%s\"). This is bad, but merging anyways..."%(kDef.name,kDef.getAddress(),kDef.depex))
				for sel in kDef.selections.getList():
					if not addrmatch.selections.hasName(sel.name):
						_log.debug("New knob has Option Text that didn't exist on original kDef. Adding selections (sel.name=\"%s\" & sel.value=0x%x"%(sel.name,sel.value))
						addrmatch.selections._addSelection(sel.value, sel.name)
					elif sel.value not in addrmatch.selections.name2value(sel.name):
						_log.error("Error: Cannot Merge Aliased knob due to selection text match, but Value is different. (kDef.name='%s' kDef.selection.name='%s' existing: 0x%x / new: 0x%x)"%(kDef.name, sel.name,nameMatch.selections.name2value(sel.name)[0],sel.value))
						self._broken.append(kDef)
						return 1
			else: # uniquename == True
				kDef._value = _weakref.proxy(self._valueMap[hash(kDef)])
				self._knobs[kDef.name]=kDef
				self._names.append(kDef.name)
		return 0
		
	def _update(self, nvUpdated,updateVals=True,updateDefs=True):
		if updateVals:
			for adr in nvUpdated._valueMap.keys():
				if self._valueMap.has_key(adr):
#					if overrideCurrentVal:
#						self._valueMap[adr].getCurrent() = nvUpdated._valueMap[adr].getCurrent()
#					if ovverrideInitialVal:
#						self._valueMap[adr].getInitial = nvUpdated._valueMap[adr].getInitial()
					assert self._valueMap[adr] == nvUpdated._valueMap[adr]
		if updateDefs:
			for knob in nvUpdated:
				if len(self.searchNames(knob.name,exact=True)) == 0:
					_log.info("NVRAM: When updating NVRAM, found a new knob. Adding it! (name = %s)"%knob.name)
					knobVal=KnobValue(current = knob._value.getCurrent(), initial=knob._value.getInitial(), default=knob._value.getDefault())
					self._addKnob(knob,knobVal)
				else:
					_log.error("NVRAM: You did not find a knob in the updated value structure. This is probably a bad thing (address = %s)"%(knob.getAddress()))
		self._version=nvUpdated._version
		return 0
	
	def _dirtyCleanup(self):
		map(KnobValue.clearDirty, self._valueMap.values())
		
	def writeDefaults(self):
		map(lambda x: x.setCurrent(x.getDefault()),self._valueMap.values())
	
	def _getDirty(self,delta=False):
		return filter(lambda knobDef: knobDef._isDirty(delta=delta), iter(self))
		
	def _getSideEffect(self):
		global _SideEffectVal
		return _SideEffectVal

	def _EnableCpuSvPatch(self):
		global _CpuSvFlexconFlow
		_CpuSvFlexconFlow = True

	def _DisableCpuSvPatch(self):
		global _CpuSvFlexconFlow
		_CpuSvFlexconFlow = False
#################################

def writeGbtFile(nvram, file="flexcon.gbt"):
	ret = 0
	fh = open(file,"w")
	
	assert issubclass(nvram.__class__, NVRAM), "Invalid object passed into writeGbtFile (type(nvram)=\"%s\")"%str(type(nvram))
	fh.write("<SYSTEM>\n")
	fh.write("\t<CPUSVBIOS VERSION=\"%s\"/>\n"%nvram.getVersion())
	fh.write("\t<biosknobs>\n")
	kattrlist=["type","setupType","name","varstoreIndex","prompt","description","size","offset","depex"]
	for knobDef in nvram._knobs:
		tmpstr="\t\t<knob  "
		tmpstr+= " ".join(map(lambda x: "%s=\"%s\""%(x,knobDef.__dict__[x]) if _pu.isString(knobDef.__dict__[x]) else "%s=\"0x%x\""%(x,knobDef.__dict__[x]),kattrlist))
		tmpstr+= " default=\"0x%02x\""%knobDef._value.getDefault()
		tmpstr+= " CurrentVal=\"0x%x\""%knobDef.getValue()
		if knobDef.setupType == "oneof":
			tmpstr+=">\n"
			tmpstr+="\t\t\t<options>\n"
			for sel in map(lambda k:"text=\"%s\" value=\"0x%x\""%(knobDef.name,knobDef.value),knobDef.selections):
				tmpstr+="\t\t\t\t<option %s/>\n"%sel
			tmpstr+="\t\t\t</options>\n"
			tmpstr+="\t\t</knob>\n"
		elif knobDef.setupType == "numeric":
		#min="0x0" max="0x17" step="1"
			for sel in knobDef.selections:
				if sel.name == "Minimum":
					tmpstr+=" min=\"0x%x\""%sel.value
				elif sel.name == "Maximum":
					tmpstr+=" max=\"0x%x\""%sel.value
				elif sel.name == "Step":
					tmpstr+=" step=\"0x%x\""%sel.value
			tmpstr+="/>\n"
		else: # knobDef.setupType in ["numeric","checkbox"]:
			tmpstr+="/>\n"
		fh.write(tmpstr)
	fh.write("\t</biosknobs>\n")
	fh.write("</SYSTEM>\n")
	fh.close()
	return ret

def readGbtFile(xmlFile, init=True):
	nvram = gbtNVRAM(file=xmlFile)
	if _parseGbtFile(nvram,xmlFile,init) != 0:
		_log.info("Error parsing the specified Gbt XML file (file:%s)"%xmlFile)
	return nvram

def _parseGbtFile(nvram, xmlFile, init=True):
	badknobs = 0
	
	assert _os.path.exists(xmlFile),"Specified file into readGbtFile doesn't exist (%s)"%xmlFile
	#assert xmlFile[-4:] == ".xml", "Specified file isn't an XML file (%s)"%file
	
	_log.debug("Parsing file: %s"%xmlFile)
	tree = ET.parse(xmlFile)
	root=tree.getroot()
	assert root.tag=="SYSTEM","Invalid root object \"%s\". Should be \"SYSTEM\""%root.tag
	
	nvram._version = None
	cpusvbios = root.find("CPUSVBIOS")
	if cpusvbios != None:
		for key,value in cpusvbios.items():
			if key.lower() == "version":
				nvram._version = value
	
	#get BIOS Map
	setupknobs=root.find("biosknobs") # early versions called it setupknobs, later it will be KnobDefinitions
	if setupknobs == None: # XML setupknobs header missing or change to KnobDefinitions has taken place
		setupknobs=root.find("KnobDefinitions")
		assert setupknobs != None, "readGbtFile: XML tree branch (setupknobs/KnobDefinitions) was not found"
		
	allKnobs=setupknobs.getchildren()
	totalKnobCount=len(allKnobs)
	currentKnobIter=0
	lStr=""
	for xmlKnob in allKnobs:
		knob = KnobDefinition()
		address = KnobAddressVIO()
		bustedKnob=False
		for key,value in xmlKnob.items():
			key = key.strip()
			if key in ["default"]:
				valDefault = _pu.str2long(value,10)
			elif key in ["CurrentVal"]:
				valInitial = _pu.str2long(value,10)
			elif key in ["setupType"]:
				if value == "numric":
					value = "numeric"
				knob.setupType = value.lower()
			elif key in ["varstoreIndex","size","offset"]:
				setattr(address,key,_pu.str2long(value,10))
			elif key in knob.__dict__.keys():
				setattr(knob,key,value)
			elif key in ["min","max","step"]:
				# These are used by numeric type, so lets ignore them.
				continue
			else:
				_log.info("nvram.readGbtFile: Found unknown key when parsing GBT XML file (<knob  ... \"%s\"=\"%s\" ... "%(key,value))
		knob._setAddress(address)
		currentKnobIter+=1
		if _debug:
			_sys.stdout.write("%s\r"%(len(lStr)*" "))
			lStr="Knob %%%ii/%%%ii: %%s"%(len("%i"%totalKnobCount),len("%i"%totalKnobCount))%(currentKnobIter,totalKnobCount,knob.name)
			_sys.stdout.write("%s\r"%lStr)
		kValue = KnobValue(default=valDefault,initial=valInitial)
		
		if knob.setupType == "oneof":
			lname=[]
			for option in xmlKnob.getchildren():
				if option.tag.strip() == "options":
					for key,value in option.items():
						if key in ["depex"]:
							knob.selections.depex.append(value)
					for attr in option.getchildren():
						tmptxt=attr.get("text").strip()
						tmpval=_pu.str2long(attr.get("value"),10)
						if tmptxt in ["",None]:
							_log.result("Warning: Bios Option \"%s\" has a selection that doesn't contain any characters. Replacing with hex string of value (name=\"0x%x\")"%(knob.name, tmpval))
							tmptxt="0x%x"%tmpval
						if tmptxt in ["Reserved", "Rsvd"]:
							_log.result("Warning: Bios Option \"%s\" has a selection named \"Reserved\" or \"Rsvd\". Appending the hex value to the end (name=\"%s (0x%x)\")"%(knob.name, tmptxt, tmpval))
							tmptxt+=" (0x%x)"%tmpval
						if knob.selections.hasName(tmptxt):
							if knob.selections.name2value(tmptxt)[0] == tmpval:
								continue
							_log.error("Error: Knob \"%s\" has multiple selection entries with the same name \"%s\" but with different values %i and %i"%(knob.name, tmptxt,knob.selections.name2value(tmptxt)[0], tmpval))
							bustedKnob=True
						else:
							knob.selections._addSelection(tmpval,tmptxt)
				else:
					_log.result("Info: Found Unexpected tag in GBT XML (tag = \"%s\")"%option.tag)
		elif knob.setupType == "checkbox":
			knob.selections._addSelection(1,"Checked")
			knob.selections._addSelection(0,"Unchecked")
		elif knob.setupType == "numeric":
			knob.selections._addSelection(_pu.str2long(xmlKnob.get("min"),10),"Minimum")
			knob.selections._addSelection(_pu.str2long(xmlKnob.get("max"),10),"Maximum")
			knob.selections._addSelection(_pu.str2long(xmlKnob.get("step"),10),"Step")
		elif knob.setupType == "legacy":
			_log.info("Info: Skipping Legacy Knob \"%s\""%knob.name)
			continue
		elif knob.setupType == "readonly":
			_log.info("Info: Skipping ReadOnly Knob \"%s\""%knob.name)
			continue
		else:
			_log.result("Error: Knob \"%s\" does not have a valid setupType (%s). Skipping."%(knob.name,knob.setupType))
			bustedKnob=True
		if len(filter(None,knob.selections.getNames())) == 0:
			_log.error("WARNING: readGbtFile: Could not add knob \"%s\" as there are no options!"%knob.name)
			bustedKnob = True

		if bustedKnob:
			nvram._broken.append(knob)
			badknobs+=1
		else:
			try:
				badknobs += nvram._addKnob(knob,kValue)
			except AssertionError,e:
				#_log.result("WARNING: readGbtFile: Could not add Bios Knob \"%s\" to NVRAM class due to parsing error. %s."%(knob.name,e))
				_log.error("WARNING: readGbtFile: Could not add Bios Knob \"%s\" to NVRAM class due to parsing error. %s."%(knob.name,e))
				badknobs += 1
	if _debug:
		_sys.stdout.write("%s\r"%(len(lStr)*" "))
	return badknobs

def _gbtGenMailbox(knoblist, binfile="gbt.bin"):
	buffer_str=""
	END_OF_BUFFER ='F4FBD0E9'

	# lambda function to turn hex number into list of hex bytes of specified size.  Use for building mailbox packet
	# zfill upper portion of a hex number to make even up to size, then turn into hexlified reversed list. size must be even.
	# Usage:  hex_ext_fcn(0x1020304, 10) --> ['\x00', '\x01', '\x02', '\x03', '\x04']
	hex_ext_fcn=lambda value,size: list(_binascii.unhexlify(hex(value)[2:].strip("L").zfill(size)))[::-1]

	bufferList=[]
	for knob in knoblist:
		binLine=[]
		# Build a list hex bytes that represents a CLI_PROCESS_BIOS_KNOBS_RQST_PARAM
		address=knob.getAddress()
		binLine.extend(hex_ext_fcn(address.varstoreIndex, 2))
		binLine.extend(hex_ext_fcn(address.offset, 4))
		binLine.extend(hex_ext_fcn(address.size, 2))
		#binLine.extend(hex_ext_fcn(knob.getValue(), knob.size+knob.size%2))
		binLine.extend(hex_ext_fcn(knob.getValue(), address.size*2))
		bufferList.append(_binascii.hexlify("".join(binLine)))

	# Compute the UINT32 parameterSize variable of CLI_BUFFER
	eLine=_binascii.hexlify(''.join(hex_ext_fcn(len(bufferList), 8)))
	bufferStr = eLine + ''.join(bufferList) + END_OF_BUFFER

	_log.info("Writing Binary File %s"%(binfile))
	BIN=open(binfile,'wb')
	BIN.writelines (_binascii.unhexlify(bufferStr))
	BIN.close()

	return(bufferStr)

class gbtNVRAM(NVRAM):
	def __init__(self, file=None):
		NVRAM.__init__(self)
		self.__dict__["_pullStub"]=file
	def pull(self,tmpfile=None):
		ret = 0
		pullFile=tmpfile
		# Should you pull live?
		if self._pullStub == None:
			if pullFile == None:
				pullFile = "pull.gbt"
			if _os.path.exists(pullFile):
				_log.info("When pulling latest GBT NVRAM, temporary file already exists! Deleting! (file:%s"%tmpfile)
				_os.remove(pullFile)
				assert not _os.path.exists(pullFile), "Error, could not delete temporary file!"
			_log.info("NVRAM: Making call to GBT to read NVRAM")
			ret |= _clb.InitInterface()
			ret |= _clb.SaveXml(pullFile, True)
			ret |= _clb.CloseInterface()
		else:
			# Else stub it!
			pullFile = self._pullStub
			if not _os.path.exists(pullFile):
				_log.error("\001ired\001Error: Cannot execute stub mode pull() without a file that exists! (file=%s)"%pullFile)
				return 1
		if ret != 0:
			_log.error("\001ired\001Error Pulling GBT File. Aborting Parsing")
			return 1
		_log.result("\001yellow\001Parsing GBT XML: \"%s\""%pullFile)
		self._clearNVdata()
		if _parseGbtFile(self, pullFile) != 0:
			_log.info("nvram.pull() failed due to XML parsing error") 
		#ret |= self._update(rawNvram,updateVals=not self._init,updateDefs=not self._init)
		#self._dirtyCleanup()
		return 0
	
	def clearcmos(self):
		#whipe CMOS
		NVRAM.clearcmos(self)
		#clear _init
	
	def push(self, binfile=None, updatedOnly=True, CmdSubType=_clb.CLI_KNOB_APPEND):
		global _gbtComandSubType
		global _gbtComandSideEffect
		ret = 0
		_clb.haltcpu()
		DRAM_MbAddr = _clb.GetDramMbAddr() # Get DRam MAilbox Address from Cmos.
		DramSharedMBbuf = _clb.memBlock(DRAM_MbAddr,0x200) # REad/save parameter buffer
		CLI_ReqBuffAddr = _clb.readclireqbufAddr(DramSharedMBbuf)  # Get CLI Request Buffer Adderss
		CLI_ResBuffAddr = _clb.readcliresbufAddr(DramSharedMBbuf)  # Get CLI Response Buffer Address
		
		if ( (CLI_ReqBuffAddr == 0) or (CLI_ResBuffAddr == 0) ):
			_log.error("GBT.push: CLI buffers are not valid or not supported, Aborting due to Error!")
			return 1
		
		# Clear CLI Command & Response buffer headers
		_clb.ClearCliBuff(CLI_ReqBuffAddr, CLI_ResBuffAddr)
		_log.info("CLI Request Buffer Addr = 0x%X   CLI Response Buffer Addr = 0x%X" %(CLI_ReqBuffAddr, CLI_ResBuffAddr))

		if binfile == None:
			binfile="push.bin"
		
		if updatedOnly:
			knoblist = self._getDirty()
		else:
			knoblist = self._knobs
		
		if len(knoblist) == 0:
			_log.result("NVRAM.push(): Nothing to do! Exitting successfully!")
			return 0
		if (CmdSubType != _clb.CLI_KNOB_LOAD_DEFAULTS):
			# TODO:  genMailboxParams should be able to replace this prs dependency and write on function in this file
			tmpBuff = _gbtGenMailbox(knoblist, binfile)
			_log.info("Loading Mailbox Params using binfile.")
			_log.info("CLI Request Buffer Addr = 0x%X   READY_PARAMSZ_OFF = 0x%X" %(CLI_ReqBuffAddr, _clb.CLI_REQ_RES_READY_PARAMSZ_OFF))
			# TODO:  Nice if could just write the tmpBuff direct without creating a bin file first, but will take some work
			_clb.load_data(binfile, CLI_ReqBuffAddr+_clb.CLI_REQ_RES_READY_PARAMSZ_OFF)

		if (CmdSubType == _clb.CLI_KNOB_APPEND):
			_clb.memwrite( CLI_ReqBuffAddr + _clb.CLI_REQ_RES_READY_CMD_OFF, 4, _clb.APPEND_BIOS_KNOBS_CMD_ID)
		elif (CmdSubType == _clb.CLI_KNOB_RESTORE_MODIFY):
			_clb.memwrite( CLI_ReqBuffAddr + _clb.CLI_REQ_RES_READY_CMD_OFF, 4, _clb.RESTOREMODIFY_KNOBS_CMD_ID)
		elif (CmdSubType == _clb.CLI_KNOB_READ_ONLY):
			_clb.memwrite( CLI_ReqBuffAddr + _clb.CLI_REQ_RES_READY_CMD_OFF, 4, _clb.READ_BIOS_KNOBS_CMD_ID)
		elif (CmdSubType == _clb.CLI_KNOB_LOAD_DEFAULTS):
			_clb.memwrite( CLI_ReqBuffAddr + _clb.CLI_REQ_RES_READY_CMD_OFF, 4, _clb.LOAD_DEFAULT_KNOBS_CMD_ID)
		
		_clb.memwrite( CLI_ReqBuffAddr + _clb.CLI_REQ_RES_READY_SIG_OFF, 4, _clb.CLI_REQ_READY_SIG )
		_log.info("CLI Mailbox programmed, now issuing S/W SMI to program knobs..")

		Status = _clb.TriggerXmlCliEntry()	# trigger S/W SMI for CLI Entry
		if(Status):
			_log.error("Error while triggering CLI Entry Point, Aborting....")
			_clb.runcpu()
			return 1

		# Verify the knob override worked from CLI point of view
		_time.sleep(3)
		_clb.haltcpu()

		offset=0
		ResHeaderbuff = _clb.memBlock(CLI_ResBuffAddr, _clb.CLI_REQ_RES_BUFF_HEADER_SIZE)
		ResReadySig = _clb.ReadBuffer(ResHeaderbuff, _clb.CLI_REQ_RES_READY_SIG_OFF, 4, _clb.HEX)
		if (ResReadySig <> _clb.CLI_RES_READY_SIG):		   # Verify if BIOS is done with the request
			if (_clb.ReadSmbase() == 0x30000 ):
				_log.info("SM Base was relocated to the default value(0x30000), S/W SMI's wont work!")
			_log.error("CLI Response not yet ready, exiting..")
			return 1

		ResCmdId = _clb.ReadBuffer(ResHeaderbuff, _clb.CLI_REQ_RES_READY_CMD_OFF, 2, _clb.HEX)
		ResFlags = _clb.ReadBuffer(ResHeaderbuff, _clb.CLI_REQ_RES_READY_FLAGS_OFF, 2, _clb.HEX)
		ResStatus = _clb.ReadBuffer(ResHeaderbuff, _clb.CLI_REQ_RES_READY_STATUS_OFF, 4, _clb.HEX)
		ResParamSize = _clb.ReadBuffer(ResHeaderbuff, _clb.CLI_REQ_RES_READY_PARAMSZ_OFF, 4, _clb.HEX)
		_log.info("CLI Response Header:")
		_log.info("   CmdID = 0x%X;  Flags.CmdSubType = \"%s\";" %(ResCmdId, _gbtComandSubType[int((ResFlags>>6) & 0xF)]))
		_log.info("   Status = 0x%X;  ParamSize = 0x%X;  Flags.WrongParam = %X;" %(ResStatus, ResParamSize, (ResFlags & 0x1)))
		_SideEffectVal = int((ResFlags>>2) & 0xF)
		if(_CpuSvFlexconFlow):
			CpuSvMailBoxaddr = _clb.ReadBuffer(DramSharedMBbuf, _clb.CPUSV_MAILBOX_ADDR_OFF, 4, _clb.HEX)
			_clb.memwrite( (CpuSvMailBoxaddr + 0x108), 4, (0x53195E00 + _SideEffectVal))
		_log.info("   Flags.CantExe = %X;  Flags.SideEffects = \"%s\"; " %(((ResFlags>>1) & 0x1), _gbtComandSideEffect[int((ResFlags>>2) & 0xF)]))
		_log.info("CLI command executed successfully..")
		if (ResParamSize == 0):
			_log.error("CLI Response buffer's Parameter size is 0, hence returning..")
			_clb.runcpu()
			return 1

		ResParambuff = _clb.memBlock((CLI_ResBuffAddr + _clb.CLI_REQ_RES_BUFF_HEADER_SIZE), ResParamSize)
		_log.info("BIOS knobs CLI Command ended successfully, see below for the results..")
		_log.info("|--|----|------------------------------------------|--|-----------|-----------|")
		if (CmdSubType == _clb.CLI_KNOB_LOAD_DEFAULTS):
			_log.info("|VI|Ofst|                 Knob Name                |Sz|PreviousVal|RestoredVal|")
		else:
			_log.info("|VI|Ofst|                 Knob Name                |Sz|   DefVal  |   CurVal  |")
		_log.info("|--|----|------------------------------------------|--|-----------|-----------|")
		while(1):   # read and print the return knobs entry parameters from CLI's response buffer
			if (offset >= ResParamSize):
				break
			KnobEntryAdd	= _clb.ReadBuffer(ResParambuff, offset+0, 4, _clb.HEX)
			KnobEntrySize   = _clb.ReadBuffer(ResParambuff, offset+4, 2, _clb.HEX)
			KnobName	    = _clb.findKnobName(KnobEntryAdd)
			VarId           = _clb.ReadBuffer(ResParambuff, offset+6, 1, _clb.HEX)
			KnobOffset      = _clb.ReadBuffer(ResParambuff, offset+7, 2, _clb.HEX)
			Size	        = _clb.ReadBuffer(ResParambuff, offset+9, 1, _clb.HEX)
			DefVal          = _clb.ReadBuffer(ResParambuff, offset+10, Size, _clb.HEX)
			CurVal          = _clb.ReadBuffer(ResParambuff, offset+10+Size, Size, _clb.HEX)
			offset          = offset+10+(Size*2)
			_log.info("|%2X|%4X|%42s|%2X| %8X  | %8X  |" %(VarId, KnobOffset, KnobName, Size, DefVal, CurVal))
			_log.info("|--|----|------------------------------------------|--|-----------|-----------|")
		#print "final Result Buff Offset 0x%X" %(offset)
		_clb.runcpu()
		self._dirtyCleanup()
		return ret
	
	def verify(self):
		assert False, "Verify for GBT not yet written"
		ret = 0
		return ret

	def write(self, file="flexcon.gbt"):
		writeGbtFile(self,file)
