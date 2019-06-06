#!/usr/bin/env python
# Cscripts remove start
#-------------------------------------------------------------------------------
# Name:        XmlIniParser.py
# Purpose:     To generate biosdata.bin file from biosknobs.ini and biosKnobs.xml file
# Author:      ashinde(amol.shinde@intel.com)
#-------------------------------------------------------------------------------
__author__ = 'amol.shinde@intel.com'
# Cscripts remove end
import sys,re,os,copy
import xml.etree.ElementTree as ET
import binascii
import datetime
import types

# Global variable
#-------------------
tree=None
mydebug=1
sigFlag=0
setupFlag=0
#sign-->setup--> valid
setupMap={0:{0:'biosknobs',1:'biosknobs'},1:{0:'setupknobs',1:'biosknobs'}}
# nvar_*_size--> default value -->corrected value
nvarMap={}
ExitOnAlienKnobs=False

# User defined Function
#-----------------------
def nstrip(strg,nonetype=''):
	if strg is not None:
		return(strg.strip())
	else:
		return(nonetype)

def calUqival(data):
	if data.lower() not in ['null',''] and data is not None:
		j=0
		total_str=''
		while j<len(data):
			each_bit=binascii.hexlify(data[j]).zfill(4)+' '
			total_str=total_str+each_bit
			j=j+1
		if len(data)>=5:
			total_str='Q 0005 '+total_str
		return (total_str)
	else:
		return (data)

def populateNvarCorr(xmlFile='biosKnobs.xml'):
	global nvarMap
	global tree
	if tree is None:
		tree = ET.parse(xmlFile)
	re_nvar=re.compile('Nvar_(.*)_Size')
	Offset = 0x100
	for SetupKnobs in tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			if (SETUPTYPE == "STRING"):
				continue
			name = (nstrip(BiosKnob.get("name")))
			default = int((nstrip(BiosKnob.get("default"))),16)
			x1 = re.search(re_nvar,name)
			if SETUPTYPE in ['LEGACY']:
				if x1 is not None:
					nvarIndex=int(x1.group(1))
					nvarMap[nvarIndex]={'NvarSize':default,'correction':Offset}
					Offset = Offset + nvarMap[nvarIndex]['NvarSize']
	if (Offset > 0x100):
		nvarIndex = nvarIndex + 1
		nvarMap[nvarIndex]={'NvarSize':0x00,'correction':Offset}
	print "Nvar value Corrected"
	#print nvarMap

def getSetupTag(xmlFile):
	global tree
	global setupMap
	global setupFlag
	global sigFlag
	if tree is None:
		tree = ET.parse(xmlFile)
	sigFlag=0xF
	setupFlag=0xF
	for SetupKnobs in tree.getiterator(tag="biosknobs"):
		sigFlag=0
		setupFlag=0
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			name = (nstrip(BiosKnob.get("name")))
			if name in ['Signature']:
				sigFlag=1
				if SETUPTYPE in ['LEGACY']:
					setupFlag=1
				break

	if sigFlag == 0xF and setupFlag == 0xF:
		setupTag='setupknobs'   # this means <biosknobs> tag was not found in the XML
	else:
		setupTag=setupMap[sigFlag][setupFlag]

	if sigFlag == 1 and setupFlag == 1:
		print "Found XML Knobs in Ganges format"
		populateNvarCorr(xmlFile='biosKnobs.xml')

	# print "Parsing [%s] section in xml" %setupTag
	return(setupTag)

def getBiosLookup(xmlFile='biosKnobs.xml', force_parse_xml=False):
	global tree
	if tree is None:
		tree = ET.parse(xmlFile)
	elif force_parse_xml == True:
		tree = ET.parse(xmlFile)
	setuptag=getSetupTag(xmlFile)
	biosMap={}
	for SetupKnobs in tree.getiterator(tag=setuptag):
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			if SETUPTYPE in ["CHECKBOX","NUMRIC" ,"NUMERIC","ONEOF","STRING"]:
				biosMap[nstrip(BiosKnob.get("name"))]={'size':nstrip(BiosKnob.get("size")),'offset':nstrip(BiosKnob.get("offset")),'vstore':nstrip(BiosKnob.get("varstoreIndex", "0xFF")), 'CurrentVal':nstrip(BiosKnob.get("CurrentVal"))}
			elif SETUPTYPE not in ["LEGACY", "READONLY"] :
				print "Setup Type is unknown (Need to add this) biosName[%s] setupType[%s]. " %(nstrip(BiosKnob.get("name")),SETUPTYPE)
	# print "Lookup Prepared !! len[%s]" %str(len(biosMap ))
	return(biosMap)

def getCpuSvBiosLookup(xmlFile='biosKnobs.xml'):
	global tree
	if tree is None:
		tree = ET.parse(xmlFile)
	setuptag='biosknobs'
	biosMap={}
	offsetMap={}
	for SetupKnobs in tree.getiterator(tag=setuptag):
		for BiosKnob in SetupKnobs.getchildren():
			KNOBTYPE = (nstrip(BiosKnob.get("type"))).upper()
			if KNOBTYPE in ["SCALAR"]:
				if not biosMap.has_key(nstrip(BiosKnob.get("name"))):
					biosMap[nstrip(BiosKnob.get("name"))]=nstrip(BiosKnob.get("offset"))
					offsetMap[nstrip(BiosKnob.get("offset"))]={'name':nstrip(BiosKnob.get("name")),'size':nstrip(BiosKnob.get("size")),'offset':nstrip(BiosKnob.get("offset")),'default':nstrip(BiosKnob.get("default"))}
				else:
					print "  Warning - Duplicate Knobs : %s " %nstrip(BiosKnob.get("name"))
	print "Lookup Prepared !! len[%s]" %str(len(biosMap ))
	return(biosMap,offsetMap)

def getBiosini(fname):
	INI=open(fname)
	biosiniList=INI.readlines()
	INI.close()
	iniList={}
	knobStart=0
	i=0
	asitislist=[]
	while i< len(biosiniList):
		line=biosiniList[i]
		if line.strip() == '[BiosKnobs]':
			knobStart=1
			i=i+1
			continue
		elif line.strip() == '[Softstraps]':
			knobStart=0    #to end BiosKnobs section -Added by Cscripts tool
		if knobStart==1:
			knobName=knobValue=''
			line=line.split(';')[0]
			if line.strip() <> '':
				(knobName,knobValue)= line.split('=')
				iniList[knobName.strip()]=knobValue.strip()
				asitislist.append( knobName.strip())
		i=i+1
	return(iniList,asitislist)

def offsetCorr(knobOffset_hex,knobVstore_hex):
	knobOffset_hex_format='0x'+knobOffset_hex
	knobVstore_hex_format='0x'+knobVstore_hex
	global nvarMap
	offsetCorr=int(knobOffset_hex_format,16) -nvarMap[int(knobVstore_hex_format,16)]['correction']
	offserCorr_format=hex(offsetCorr)[2:].zfill(4)
	return(offserCorr_format)

def createBinFile(bin_f_name,biosmap,inimap,asitis):
	"""
	abc = "0012" abc = 0x32313030
	abc = L"0012" abc = 0x0032003100300030
	abc = 123 abc = 0x7B
	abc = 0x123 abc = 0x123
	"""
	#toxls[knob_key]={'min': knob_min, 'max': knob_max, 'knobName':knob_name,'vstore':knob_vstore,'size':knob_size,'offset':knob_offset}
	global setupFlag, sigFlag, ExitOnAlienKnobs
	Number_of_entries =0
	END_OF_BUFFER ='F4FBD0E9'
	bufferList=[]
	AlienKnobsFound = False
	for knob in asitis:
		if biosmap.has_key(knob):
			knobVal_hex='00'
			knobSize_int=0
			knobOffset_hex='0000'
			knobVstore_hex='00'
			knobSize_hex='00'
			knobVal=inimap[knob]
			knobSize=biosmap[knob]['size']
			knobOffset=biosmap[knob]['offset']
			knobVstore=biosmap[knob]['vstore']
			a1=re.search('0x(.*)',knobVal)
			a2=re.search('L"(.*)"',knobVal)
			a3=re.search('"(.*)"',knobVal)
			b1=re.search('0x(.*)',knobSize)
			c1=re.search('0x(.*)',knobVstore)
			d1=re.search('0x(.*)',knobOffset)
			if a1 is not None:
				knobVal_hex=a1.group(1)
			elif a2 is not None:
				j=0
				data =a2.group(1).strip()[::-1]
				total_str=''
				while j<len(data):
					each_bit = '00' + binascii.hexlify(data[j]).zfill(2)
					total_str = total_str + each_bit
					j=j+1
				knobVal_hex=total_str
			elif a3 is not None:
				knobVal_hex=binascii.hexlify(a3.group(1).strip()[::-1])
			else:
				if knobVal.isdigit() :
					knobVal_hex=hex(int(knobVal))[2:]
				else:
					print " Knob [%s] value [%s] is not in proper format" %(knob,knobVal)
					continue
			if b1 is not None:
				knobSize_hex =b1.group(1).zfill(2)
				knobSize_int=int('0x'+knobSize_hex )
			else:
				knobSize_hex =hex(int(knobSize))[2:].zfill(2)
				knobSize_int=int(knobSize)
			if c1 is not None:
				knobVstore_hex=c1.group(1).zfill(2)
			else:
				knobVstore_hex =hex(int(knobVstore))[2:].zfill(2)
			if d1 is not None:
				knobOffset_hex =d1.group(1).zfill(4)
			else:
				knobOffset_hex =hex(int(knobOffset))[2:].zfill(4)

			if setupFlag == 1 and sigFlag == 1:
				if ( int('0x'+knobVstore_hex,16) != 0xFF ):
					knobOffset_hex = offsetCorr(knobOffset_hex,knobVstore_hex)
			if int(knobSize_int*2) < len(knobVal_hex):
				print "Value [%s] of knob [%s] mentioned size[%s] is larger than mentioned size[%s] in xml" %(knobVal,knob,(len(knobVal_hex)/2),knobSize )
				continue
			else:
				knobVal_hex=knobVal_hex.zfill(knobSize_int*2)
		else:
			print "Bios Knob \"%s\" does not currently exist " %knob
			AlienKnobsFound = True
			continue
		valueLine=''
		tbl_desc_line=[]
		inc=knobSize_int*2
		while inc>0:
			tbl_desc_line.append(knobVal_hex[inc-2:inc])
			inc= inc-2
		valueLine =''.join(tbl_desc_line)
		binline=knobVstore_hex.strip() + knobOffset_hex[2:].strip()+knobOffset_hex[0:2].strip()+knobSize_hex.strip()+valueLine.strip()
		binline_ascii=binline#binascii.unhexlify(binline)
		#binline_ascii=binline=binascii.unhexlify(knobVstore_hex.strip()) + binascii.unhexlify(knobOffset_hex[2:].strip())+binascii.unhexlify(knobOffset_hex[0:2].strip())+binascii.unhexlify(knobSize_hex.strip())+binascii.unhexlify(valueLine.strip())
		#print ("knob[%s] \t binline [%s] \t binline_ascii[%s]" %(knob,binline ,binline_ascii ))
		bufferList.append(binline_ascii)

	if(ExitOnAlienKnobs and AlienKnobsFound):
		print "Aborting Since ExitOnAlienKnob was set, see above for details. "
		return ''

	BIN=open(bin_f_name,'wb')
	Number_of_entries = hex(len(bufferList))[2:].zfill(8)
	inc=8
	entries_line=[]
	while inc>0:
		entries_line.append(Number_of_entries[inc-2:inc])
		inc= inc-2
	eLine =''.join(entries_line)
	buffer_str=eLine+''.join(bufferList)+END_OF_BUFFER
	ReqBuff = binascii.unhexlify(buffer_str)
	BIN.writelines(ReqBuff)
	BIN.close()
	# print "Bin file Created !!"
	return(ReqBuff)

def corrValue2hex(val):
	val_hex=''
	a1=re.search('0x(.*)',val)
	a2=re.search('L"(.*)"',val)
	a3=re.search('"(.*)"',val)
	if a1 is not None:
		val_hex=a1.group(1)
	elif a2 is not None:
		j=0
		data =a2.group(1)
		total_str=''
		while j<len(data):
			each_bit=binascii.hexlify(data[j]).zfill(4)+' '
			total_str=total_str+each_bit
			j=j+1
		val_hex =total_str

	elif a3 is not None:
		val_hex=binascii.hexlify(a3.group(1))
	else:
		if val.isdigit() :
			val_hex=hex(int(val))[2:]
	val_hex='0x'+val_hex
	return(val_hex)

def modfyValue(inimap,biosmap,offsetmap):
	for knob in inimap:
		if biosmap.has_key(knob):
			size=offsetmap[biosmap[knob]]['size']
			value=inimap[knob]
			value_corr=corrValue2hex(value)
			size_corr=corrValue2hex(size)
			#print "Value [%s] mentioned for knob [%s] is exceeding size [%s] mentioned in XML.." %(value_corr,knob,size_corr)
			if int(value_corr,16)>=(2**(int(size_corr,16)*8)):
				print "Value [%s] mentioned for knob [%s] is exceeding size [%s] mentioned in XML.." %(value_corr,knob,size_corr)
			else:
				offsetmap[biosmap[knob]]['default']=value_corr
		else:
		    print "Knob [%s] Mentioned in INI file doesn't exists in XML.." % knob
	return(offsetmap)

def parseCliinixml(f_name, ini_f_name, binfile="bios.bin"):
	global tree
	tree = None
	biosmap=getBiosLookup(f_name)
	inimap,asitis=getBiosini(ini_f_name)
	return(createBinFile(binfile,biosmap,inimap,asitis))

def createCpuSvBinFile(binfile,biosmap,offsetmapMod):
	offsetList_sort=sorted(offsetmapMod.keys())
	#print offsetList_sort
	i=0
	towrite=''
	while (i<len(offsetList_sort)):
		cur_offset=corrValue2hex(offsetList_sort[i])
		cur_size=corrValue2hex(offsetmapMod[offsetList_sort[i]]['size'])
		value = corrValue2hex(offsetmapMod[offsetList_sort[i]]['default'])[2:]
		old_size='0x0'
		old_offset= '0x0'
		if i==0:
			pass
		else :
			old_offset=corrValue2hex(offsetList_sort[i-1])
			old_size=corrValue2hex(offsetmapMod[offsetList_sort[i-1]]['size'])
		tobeoffset= int(old_offset,16) + int(old_size,16)
		hole_pad = int(cur_offset,16) - tobeoffset
		if ( hole_pad >= 0):
			valueLine=''
			cur_pad=int(cur_size,16)
			knobVal_hex = value.zfill(cur_pad*2)
			tbl_desc_line=[]
			inc=int(cur_size,16)*2
			while inc>0:
				tbl_desc_line.append(knobVal_hex[inc-2:inc])
				inc= inc-2
			valueLine =''.join(tbl_desc_line)
			towrite+=''.zfill(hole_pad*2)+valueLine
		else :
			print "knob [%s] offset [%s] is overlapping with knob [%s] offset [%s].. hence exiting.." %(offsetmapMod[offsetList_sort[i-1]]['name'],offsetList_sort[i-1],offsetmapMod[offsetList_sort[i]]['name'],offsetList_sort[i])
			return(0x1)
		i+=1
	towrite
	BIN=open(binfile,'wb')
	BIN.writelines(binascii.unhexlify(towrite))
	BIN.close()

#parseCliinixml ('PlatformConfig_IVT.xml','BiosKnobs.ini')
def parseGangesinixml(f_name, ini_f_name, binfile="bios.bin"):
	global tree
	tree = None
	(biosmap,offsetmap)=getCpuSvBiosLookup(f_name)
	inimap,asitis=getBiosini(ini_f_name)
	offsetmapMod =modfyValue(inimap,biosmap,offsetmap)
	return(createCpuSvBinFile(binfile,biosmap,offsetmapMod))

def genCSV(xmlfile):
	global tree
	duplicateKnobs=[]
	invalidOption={}
	nullUQI=[]
	notKnownType=[]
	knobList={}
	tree = None
	if tree is None:
		tree = ET.parse(xmlfile)

	_BIOSVERSION=''
	for Version in tree.getiterator(tag="BIOS"):
		_BIOSVERSION = Version.get('VERSION')
	if (_BIOSVERSION == ''):
		for Version in tree.getiterator(tag="SVBIOS"):
			_BIOSVERSION = Version.get('VERSION')
	if (_BIOSVERSION == ''):
		for Version in tree.getiterator(tag="CPUSVBIOS"):
			_BIOSVERSION = Version.get('VERSION')

	print "\nBIOS XML is of VERSION [%s]" %_BIOSVERSION
	if _BIOSVERSION <> 'SVOS_EX_A0':
		csvFileName=_BIOSVERSION.replace('.','_')+'_KnobsData'+'.csv'
	basepath = os.path.dirname(xmlfile)
	csvFile = os.sep.join([basepath, csvFileName])
	RXLS =open(csvFile,'w')
	RXLS.write("Name,Description,Type,Size(Bytes),Sel,Value,DefaultVal,CurrentVal,SetupPagePtr,Depex,UQI\n")
	print "writing to file : %s" %csvFile
	for SetupKnobs in tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			if SETUPTYPE in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]:
				RXLS.write("%s,%s: %s,%s,%s,,,%s,%s,%s,%s,%s\n"%(nstrip(BiosKnob.get("name")),nstrip(BiosKnob.get("prompt")).replace(',',';'),nstrip(BiosKnob.get("description")).replace(',',';'),SETUPTYPE,nstrip(BiosKnob.get('size')), nstrip(BiosKnob.get('default')),nstrip(BiosKnob.get('CurrentVal')),nstrip(BiosKnob.get('SetupPgPtr')),nstrip(BiosKnob.get('depex')),calUqival(nstrip(BiosKnob.get("UqiVal")))))
			if SETUPTYPE == "ONEOF":
				for options in BiosKnob.getchildren():
					for option in options.getchildren():
						RXLS.write(",,,,%s,%s,,,,,\n"%(nstrip(option.get("text")),nstrip(option.get("value"))))
			elif SETUPTYPE in ["NUMRIC" ,"NUMERIC","STRING"]:
				RXLS.write(",,,,%s,%s,,,,,\n"%("min",nstrip(BiosKnob.get("min"))))
				RXLS.write(",,,,%s,%s,,,,,\n"%("max",nstrip(BiosKnob.get("max"))))
			elif SETUPTYPE in ["CHECKBOX"]:
				RXLS.write(",,,,min,0,,,,,\n")
				RXLS.write(",,,,max,1,,,,,\n")
			else:
				print "Setup Type is unknown for biosName[%s] setupType[%s]. " %(nstrip(BiosKnob.get("name")),SETUPTYPE)
				notKnownType.append(SETUPTYPE )
	RXLS.close()
	print "Csv File generated !"

def GenKnobsDelta(RefXml, MyXml, OutFile=r"KnobsDiff.log", CmpTag="default"):
	RefTree = ET.parse(RefXml)
	MyTree = ET.parse(MyXml)
	RefKnobsDict = {}
	MyKnobsDict = {}
	BiosTag = ["BIOS", "SVBIOS", "CPUSVBIOS"]
	RefKnobsBiosVer = ""
	MyKnobsBiosVer = ""
	IntCompare = False
	if( (CmpTag == "default") or (CmpTag == "CurrentVal") or (CmpTag == "offset") ):
		IntCompare = True

	for count in range (0, 3):
		if (RefKnobsBiosVer == ""):
			for RefXmlBios in RefTree.getiterator(tag=BiosTag[count]):
				RefKnobsBiosVer = nstrip(RefXmlBios.get('VERSION'))
				break

	for count in range (0, 3):
		if (MyKnobsBiosVer == ""):
			for MyXmlBios in MyTree.getiterator(tag=BiosTag[count]):
				MyKnobsBiosVer = nstrip(MyXmlBios.get('VERSION'))
				break

	for RefSetupKnobs in RefTree.getiterator(tag="biosknobs"):
		for RefBiosKnob in RefSetupKnobs.getchildren():
			REF_SETUPTYPE = (nstrip(RefBiosKnob.get("setupType"))).upper()
			if REF_SETUPTYPE in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]:
				RefOffset = int(nstrip(RefBiosKnob.get('offset')), 16)
				RefKnobName = nstrip(RefBiosKnob.get('name'))
				if(IntCompare):
					RefCmpVal = int(nstrip(RefBiosKnob.get(CmpTag)), 16)
				else:
					RefCmpVal = nstrip(RefBiosKnob.get(CmpTag))
				infoList=[]
				infoList.append(RefOffset)
				infoList.append(RefCmpVal)
				RefKnobsDict[RefKnobName] = infoList
	for MySetupKnobs in MyTree.getiterator(tag="biosknobs"):
		for MyBiosKnob in MySetupKnobs.getchildren():
			CURR_SETUPTYPE = (nstrip(MyBiosKnob.get("setupType"))).upper()
			if CURR_SETUPTYPE in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]:
				MyOffset = int(nstrip(MyBiosKnob.get('offset')), 16)
				MyKnobName = nstrip(MyBiosKnob.get('name'))
				if(IntCompare):
					MyCmpVal = int(nstrip(MyBiosKnob.get(CmpTag)), 16)
				else:
					MyCmpVal = nstrip(MyBiosKnob.get(CmpTag))
				infoList=[]
				infoList.append(MyOffset)
				infoList.append(MyCmpVal)
				MyKnobsDict[MyKnobName] = infoList

	out = open(OutFile,'w')
	print"\n\nWriting delta knobs for comparing following field \"%s\"\n   RefXmlBiosVer = %s \n   MyXmlBiosVer = %s " %(CmpTag, RefKnobsBiosVer, MyKnobsBiosVer)
	print"----------------------------------|--------------------|--------------------|"
	print"                Knob Name         |    RefXmlDefVal    |    MyXmlDefVal     |"
	print"----------------------------------|--------------------|--------------------|"
	out.write("\n\nWriting delta knobs for comparing following field \"%s\"\n   RefXmlBiosVer = %s \n   MyXmlBiosVer = %s \n" %(CmpTag, RefKnobsBiosVer, MyKnobsBiosVer))
	out.write("----------------------------------|--------------------|--------------------|\n")
	out.write("                Knob Name         |    RefXmlDefVal    |    MyXmlDefVal     |\n")
	out.write("----------------------------------|--------------------|--------------------|\n")
	for BiosKnob in RefKnobsDict:
		if(IntCompare):
			RefStrVal = "0x%X" %RefKnobsDict[BiosKnob][1]
		else:
			RefStrVal = RefKnobsDict[BiosKnob][1]
		try:
			if(IntCompare):
				MyStrVal = "0x%X" %MyKnobsDict[BiosKnob][1]
			else:
				MyStrVal = MyKnobsDict[BiosKnob][1]
		except KeyError:
			MyStrVal = "  ---  N.A. ---  "
		if(RefStrVal != MyStrVal):
			print " %32s | %18s | %-18s |" %(BiosKnob, RefStrVal, MyStrVal)
			out.write(" %32s | %18s | %-18s |\n" %(BiosKnob, RefStrVal, MyStrVal))
	print"----------------------------------|--------------------|--------------------|"
	out.write("----------------------------------|--------------------|--------------------|\n")
	out.close()

def GenBiosKnobsIni(PcXml, FlexconCfgFile, KnobsIniFile):
	Tree = ET.parse(PcXml)
	BiosKnobsDict={}
	for SetupKnobs in Tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			KnobName = nstrip(BiosKnob.get('name'))
			BiosKnobsDict[KnobName] = {}
			BiosKnobsDict[KnobName]["$SetUpType"] = SETUPTYPE
			if SETUPTYPE == "ONEOF":
				for options in BiosKnob.getchildren():
					for option in options.getchildren():
						BiosKnobsDict[KnobName][nstrip(option.get("text"))] = nstrip(option.get("value"))
	INI=open(FlexconCfgFile)
	biosiniList=INI.readlines()
	INI.close()
	knobStart=0
	i=0
	asitislist=[]
	OutIni = open(KnobsIniFile,'w')
	OutIni.write(";-------------------------------------------------\n")
	OutIni.write("; ESS Sv BIOS contact: amol.shinde@intel.com\n")
	OutIni.write("; XML Shared MailBox settings for SV BIOS CLI based setup\n")
	OutIni.write("; The name entry here should be identical as the name from the XML file (retain the case)\n")
	OutIni.write(";-------------------------------------------------\n")
	OutIni.write("[BiosKnobs]\n")
	while i< len(biosiniList):
		line=biosiniList[i].strip()
		if ((line == '[BIOS Overrides]') or (line == '[BiosKnobs]')):
			knobStart=1
			i=i+1
			continue
		if knobStart==1:
			knobName=knobValue=''
			line=line.split(';')[0]
			if line <> '':
				if (line[0] == '['):
					if (line[-1] == ']'):
						break
				knobName = line.split('=')[0].strip()
				knobValue = line.split('=')[1].strip()
				if(BiosKnobsDict[knobName]["$SetUpType"] == "ONEOF"):
					if (knobValue in ["Enabled", "Enable"]):
						try:
							OutIni.write("%s = %s \n" %(knobName, BiosKnobsDict[knobName]["Enabled"]))
							i=i+1
							continue
						except:
							pass
						try:
							OutIni.write("%s = %s \n" %(knobName, BiosKnobsDict[knobName]["Enable"]))
							i=i+1
							continue
						except:
							pass
					if (knobValue in ["Disabled", "Disable"]):
						try:
							OutIni.write("%s = %s \n" %(knobName, BiosKnobsDict[knobName]["Disabled"]))
							i=i+1
							continue
						except:
							pass
						try:
							OutIni.write("%s = %s \n" %(knobName, BiosKnobsDict[knobName]["Disable"]))
							i=i+1
							continue
						except:
							pass
					else:
						OutIni.write("%s = %s \n" %(knobName, BiosKnobsDict[knobName][knobValue]))
				if(BiosKnobsDict[knobName]["$SetUpType"] == "CHECKBOX"):
					if (knobValue == "Checked"):
						OutIni.write("%s = %d \n" %(knobName, 1))
					if (knobValue == "Unchecked"):
						OutIni.write("%s = %d \n" %(knobName, 0))
				if( (BiosKnobsDict[knobName]["$SetUpType"] == "NUMRIC") or (BiosKnobsDict[knobName]["$SetUpType"] == "NUMERIC") ):
					OutIni.write("%s\n" %line)
		i=i+1
	OutIni.close()

def BiosCnfGenBiosKnobsIni(PcXml, BiosConfFile, KnobsIniFile="", Mode="genbiosconf",KnobsDict={}):
	Tree = ET.parse(PcXml)
	BiosKnobsDict={}
	KnobCount = 0
	UqiXmlDict = {}
	KnobComments = {}
	KnobsStart = False
	Coment = ""
	ComentDict = {}
	for line in open(PcXml,'r').readlines():
		line=line.strip()
		if ( line == '' ):
			continue
		match = re.search(r"\s*\<biosknobs\>\s*", line)
		if(match != None):
			KnobsStart = True
		match = re.search(r"\s*\<\/biosknobs\>\s*", line)
		if(match != None):
			KnobsStart = False
		if(KnobsStart):
			match = re.search(r"\s*\<!--\s*(.*?)\s*--\>\s*", line)
			if(match != None):
				Coment = Coment + "// " + match.group(1) + "\n"
			match = re.search(r"\s*\<knob\s*(.*?)\s*name=\"(\S*)\"\s*", line)
			if(match != None):
				ComentDict[match.group(2)] = Coment
				Coment = ""
	for SetupKnobs in Tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			BiosKnobsDict[KnobCount] = {}
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			BiosKnobsDict[KnobCount]["$KnobName"] = nstrip(BiosKnob.get('name'))
			BiosKnobsDict[KnobCount]["$SetUpType"] = SETUPTYPE
			BiosKnobsDict[KnobCount]["$Prompt"] = nstrip(BiosKnob.get('prompt'))
			BiosKnobsDict[KnobCount]["$KnobSize"] = corrValue2hex(nstrip(BiosKnob.get('size')))
			BiosKnobsDict[KnobCount]["$DupUqi"] = False
			KnobUqiVal = nstrip(BiosKnob.get('UqiVal'))
			BiosKnobsDict[KnobCount]["$KnobUqi"] = KnobUqiVal
			if(UqiXmlDict.get(KnobUqiVal, -1) == -1):
				UqiXmlDict[KnobUqiVal] = KnobCount
			else:
				BiosKnobsDict[KnobCount]["$DupUqi"] = True
			if(SETUPTYPE == 'STRING'):
				BiosKnobsDict[KnobCount]["$CurVal"] = BiosKnob.get('CurrentVal')
				BiosKnobsDict[KnobCount]["$DefVal"] = BiosKnob.get('default')
			else:
				BiosKnobsDict[KnobCount]["$CurVal"] = corrValue2hex(nstrip(BiosKnob.get('CurrentVal')))
				BiosKnobsDict[KnobCount]["$DefVal"] = corrValue2hex(nstrip(BiosKnob.get('default')))
			BiosKnobsDict[KnobCount]['OptionsDict'] = {}
			if SETUPTYPE == "ONEOF":
				OptionsCount = 0
				for options in BiosKnob.getchildren():
					for option in options.getchildren():
						BiosKnobsDict[KnobCount]['OptionsDict'][OptionsCount] = { 'OptionText': nstrip(option.get("text")), 'OptionVal': corrValue2hex(nstrip(option.get("value"))) }
						OptionsCount = OptionsCount + 1
			elif SETUPTYPE in ["NUMRIC" ,"NUMERIC","STRING"]:
				BiosKnobsDict[KnobCount]['OptionsDict'][0] = { 'OptionText': 'Minimum', 'OptionVal': corrValue2hex(nstrip(BiosKnob.get("min"))) }
				BiosKnobsDict[KnobCount]['OptionsDict'][1] = { 'OptionText': 'Maximum', 'OptionVal': corrValue2hex(nstrip(BiosKnob.get("max"))) }
				BiosKnobsDict[KnobCount]['OptionsDict'][2] = { 'OptionText': 'Step', 'OptionVal': corrValue2hex(nstrip(BiosKnob.get("step"))) }
			elif SETUPTYPE in ["CHECKBOX"]:
				BiosKnobsDict[KnobCount]['OptionsDict'][0] = { 'OptionText': 'Unchecked', 'OptionVal': '0x00' }
				BiosKnobsDict[KnobCount]['OptionsDict'][1] = { 'OptionText': 'Checked', 'OptionVal': '0x01' }
			KnobCount = KnobCount + 1
	if( (Mode.lower() == "genbiosconf") or (Mode.lower() == "genbiosconfdef") ):
		OutTxtFile = open(BiosConfFile,'w')
		OutTxtFile.write("// This File was generate from XmlCli's Bios Knobs XML File\n\n")
		for KnobCount in range (0, len(BiosKnobsDict)):
			if(BiosKnobsDict[KnobCount]["$DupUqi"]):
				print "Duplicate uqi for Knob (%s), ignore this entry" %BiosKnobsDict[KnobCount]["$KnobName"]
				continue
			tempUqi = (binascii.hexlify(BiosKnobsDict[KnobCount]["$KnobUqi"])).upper()
			SETUPTYPE = BiosKnobsDict[KnobCount]["$SetUpType"].upper()
			Size = int(BiosKnobsDict[KnobCount]["$KnobSize"], 16)
			if (Mode.lower() == "genbiosconfdef"):
				ValueStr = BiosKnobsDict[KnobCount]["$DefVal"]
			else:
				ValueStr = BiosKnobsDict[KnobCount]["$CurVal"]
			if(SETUPTYPE == "STRING"):
				if(ValueStr[0:2] == '0x'):
					TempStr = ''
					for count in range (0, (len(ValueStr)-2), 4):
						if(ValueStr[count+2 : count+6] != '0000'):
							TempStr = TempStr + chr(ValueStr[count+2 : count+6])
					ValueStr = TempStr[::-1]
			else:
				ValueStr = ValueStr[2:].zfill(Size*2)
			if(ComentDict.get(BiosKnobsDict[KnobCount]["$KnobName"], "") != ""):
				OutTxtFile.write("\n%s" %ComentDict[BiosKnobsDict[KnobCount]["$KnobName"]])
			if(SETUPTYPE == 'ONEOF'):
				SETUPTYPE = 'ONE_OF'
			if (BiosKnobsDict[KnobCount]["$KnobUqi"] == ''):
				OutTxtFile.write("\n// [No UQI] %s %s // %s\n" %(SETUPTYPE,ValueStr,BiosKnobsDict[KnobCount]["$Prompt"]))
			else:
				OutTxtFile.write("\nQ 0006 00%s 00%s 00%s 00%s 00%s 00%s %s %s // %s\n" %(tempUqi[0:2],tempUqi[2:4],tempUqi[4:6],tempUqi[6:8],tempUqi[8:10],tempUqi[10:12],SETUPTYPE,ValueStr,BiosKnobsDict[KnobCount]["$Prompt"]))
			if(SETUPTYPE != 'STRING'):
				for OptionCount in range (0, len(BiosKnobsDict[KnobCount]['OptionsDict'])):
					if(SETUPTYPE == 'NUMERIC'):
						OutTxtFile.write("// %s = %s\n" %(BiosKnobsDict[KnobCount]['OptionsDict'][OptionCount]['OptionText'].ljust(7), BiosKnobsDict[KnobCount]['OptionsDict'][OptionCount]['OptionVal'][2:].zfill(Size*2)))
					else:
						OutTxtFile.write("// %s = %s\n" %(BiosKnobsDict[KnobCount]['OptionsDict'][OptionCount]['OptionVal'][2:].zfill(Size*2), BiosKnobsDict[KnobCount]['OptionsDict'][OptionCount]['OptionText']))
		OutTxtFile.close()
	if(Mode.lower() == "genknobsini"):
		print "Generating BiosKnobs.ini file from BiosConf Text File, will be writing only delta knobs"
		OutIni = open(KnobsIniFile,'w')
		OutIni.write(";-------------------------------------------------\n")
		OutIni.write("; ESS Sv BIOS contact: amol.shinde@intel.com\n")
		OutIni.write("; XML Shared MailBox settings for SV BIOS CLI based setup\n")
		OutIni.write("; The name entry here should be identical as the name from the XML file (retain the case)\n")
		OutIni.write(";-------------------------------------------------\n")
		OutIni.write("[BiosKnobs]\n")
		UqiDict = {}
		UqiCount = 0
		for line in open(BiosConfFile,'r').readlines():
			line=line.split('//')[0].strip()
			if ( line == '' ):
				continue
			match = re.search(r"\s*Q\s*0006\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)\s*", line)
			if (match != None):
				CurUqiVal = binascii.unhexlify(match.group(1))[1] + binascii.unhexlify(match.group(2))[1] + binascii.unhexlify(match.group(3))[1] + binascii.unhexlify(match.group(4))[1] + binascii.unhexlify(match.group(5))[1] + binascii.unhexlify(match.group(6))[1]
				CurVal = match.group(8)
				UqiDict[UqiCount] = {'UqiVal': CurUqiVal, 'KnobVal': CurVal}
				KnobCount = UqiXmlDict[CurUqiVal]
				if(UqiDict[UqiCount]['UqiVal'] == BiosKnobsDict[KnobCount]["$KnobUqi"]):
					SETUPTYPE = BiosKnobsDict[KnobCount]["$SetUpType"].upper()
					tempUqi = (binascii.hexlify(BiosKnobsDict[KnobCount]["$KnobUqi"])).upper()
					Size = int(BiosKnobsDict[KnobCount]["$KnobSize"], 16)
					if(SETUPTYPE == 'STRING'):
						if(UqiDict[UqiCount]['KnobVal'] != BiosKnobsDict[KnobCount]["$CurVal"]):
							OutIni.write("%s = L\"%s\"    ; Q 0006 00%s 00%s 00%s 00%s 00%s 00%s %s %s // %s\n" %(BiosKnobsDict[KnobCount]["$KnobName"], UqiDict[UqiCount]['KnobVal'], tempUqi[0:2],tempUqi[2:4],tempUqi[4:6],tempUqi[6:8],tempUqi[8:10],tempUqi[10:12],SETUPTYPE,UqiDict[UqiCount]['KnobVal'],BiosKnobsDict[KnobCount]["$Prompt"]))
					else:
						if(int(UqiDict[UqiCount]['KnobVal'], 16) != int(BiosKnobsDict[KnobCount]["$CurVal"], 16)):
							OutIni.write("%s = 0x%X    ; Q 0006 00%s 00%s 00%s 00%s 00%s 00%s %s %s // %s\n" %(BiosKnobsDict[KnobCount]["$KnobName"], int(UqiDict[UqiCount]['KnobVal'], 16), tempUqi[0:2],tempUqi[2:4],tempUqi[4:6],tempUqi[6:8],tempUqi[8:10],tempUqi[10:12],SETUPTYPE,hex(int(UqiDict[UqiCount]['KnobVal'], 16))[2:].zfill(Size*2),BiosKnobsDict[KnobCount]["$Prompt"]))
				UqiCount = UqiCount + 1
		OutIni.close()
	if(Mode.lower() == "inituqi"):
		for KnobsDictCount in range (0, len(KnobsDict)):
			for BiosKnobsDictCount in range (0, len(BiosKnobsDict)):
				if(KnobsDict[KnobsDictCount]['KnobName'] == BiosKnobsDict[BiosKnobsDictCount]["$KnobName"] ):
					if(KnobsDict[KnobsDictCount]['Size'], 16 == BiosKnobsDict[BiosKnobsDictCount]["$KnobSize"]):
						KnobsDict[KnobsDictCount]['Prompt'] = BiosKnobsDict[BiosKnobsDictCount]["$Prompt"]
						KnobsDict[KnobsDictCount]['UqiVal'] = BiosKnobsDict[BiosKnobsDictCount]["$KnobUqi"]

def GenAllKnobsIni(XmlFile, AllKnobIniFile):
	XmlTree = ET.parse(XmlFile)
	OutIni  = open(AllKnobIniFile,'w')
	OutIni.write(";-------------------------------------------------\n")
	OutIni.write("; ESS Sv BIOS contact: amol.shinde@intel.com\n")
	OutIni.write("; XML Shared MailBox settings for SV BIOS CLI based setup\n")
	OutIni.write("; The name entry here should be identical as the name from the XML file (retain the case)\n")
	OutIni.write(";-------------------------------------------------\n")
	OutIni.write("[BiosKnobs]\n")
	for SetupKnobs in XmlTree.getiterator(tag="biosknobs"):
		for RefBiosKnob in SetupKnobs.getchildren():
			REF_SETUPTYPE = (nstrip(RefBiosKnob.get("setupType"))).upper()
			Size = int(StrVal2Hex(nstrip(RefBiosKnob.get("size"))), 16)
			if REF_SETUPTYPE in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]:
				DefValue = int(nstrip(RefBiosKnob.get('default')), 16)
				KnobName = nstrip(RefBiosKnob.get('name'))
				if(DefValue):
					NewVal = 0
				else:
					NewVal = 1
				if (REF_SETUPTYPE == 'STRING'):
					OutIni.write("%s = L\"%s\" \n" %(KnobName, "IntelSrrBangaloreKarnatakaIndiaAsia"[0:((Size/2)-1)]))
				else:
					OutIni.write("%s = %d \n" %(KnobName, NewVal))
	OutIni.close()

def StrVal2Hex(StrVal):
	val_hex=''
	a1=re.search('0x(.*)',StrVal)
	a2=re.search('L"(.*)"',StrVal)
	a3=re.search('"(.*)"',StrVal)
	if a1 is not None:
		val_hex=hex(int(a1.group(1), 16))[2:].strip('L')
	elif a2 is not None:
		data =a2.group(1)
		for count in range (0, len(data)):
			val_hex=val_hex+binascii.hexlify(data[count]).ljust(4, '0')
	elif a3 is not None:
		val_hex=binascii.hexlify(a3.group(1))
	else:
		if StrVal.isdigit() :
			val_hex=hex(int(StrVal))[2:]
	return(val_hex)

def LittEndian(HexVal):
	NewStr = ''
	for count in range(0, len(HexVal), 2):
		NewStr = HexVal[count:count+2]+NewStr
	return NewStr

def GenKnobsDataBin(PcXml, KnobsIniFile, binfile, Operation="Prog"):
	Tree = ET.parse(PcXml)
	BiosKnobsDict={}
	DeltaDict={}
	for SetupKnobs in Tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			KnobName = nstrip(BiosKnob.get('name'))
			Type = (nstrip(BiosKnob.get("setupType"))).upper()
			Offset = nstrip(BiosKnob.get('offset'))
			Size = nstrip(BiosKnob.get('size'))
			VarId = nstrip(BiosKnob.get('varstoreIndex'))
			DefVal = nstrip(BiosKnob.get('default'))
			CurVal = nstrip(BiosKnob.get('CurrentVal'))
			BiosKnobsDict[KnobName] = {'VarId':VarId, 'Type':Type, 'Size': Size, 'offset':Offset, 'DefVal':DefVal, 'CurVal':CurVal}
			if(DefVal != CurVal):
				DeltaDict[KnobName] = DefVal

	ReqKnobDict={}
	if(Operation != "LoadDef"):
		knobStart=0
		for line in open(KnobsIniFile,'r').readlines():
			line=line.split(';')[0]
			line=line.strip()
			if( line == '' ):
				continue
			if(line == "[BiosKnobs]"):
				knobStart=1
				continue
			if(knobStart):
				Name = line.split('=')[0].strip()
				ReqKnobDict[Name] = line.split('=')[1].strip()
		if(Operation == "ResMod"):
			for KnobName in DeltaDict:
				if KnobName not in ReqKnobDict:
					ReqKnobDict[KnobName] = DeltaDict[KnobName]
	else:
		ReqKnobDict = DeltaDict

	BuffDict={}
	for Name in ReqKnobDict:
		try:
			Var=BiosKnobsDict[Name]['VarId']
			Ofst=BiosKnobsDict[Name]['offset']
			Sz=BiosKnobsDict[Name]['Size']
			Size=int(StrVal2Hex(Sz), 16)
			VarId=int(StrVal2Hex(Var), 16)
		except:
			print "Knob Name \"%s\" not found in XML, Skipping" %Name
			continue
		if(BiosKnobsDict[Name]['Type'] == 'STRING'):
			ReqValStr = StrVal2Hex(ReqKnobDict[Name]).ljust(Size*2, '0')
		else:
			ReqValStr = LittEndian(StrVal2Hex(ReqKnobDict[Name]).zfill(Size*2))
		if(len(ReqValStr) > (Size*2)):
			print "Requested Knob \"%s\" Value exceeds the allowed Size limit(%d char's), Ignoring this entry" %(Name, (Size/2))
			continue
		try:
			len(BuffDict[VarId])
		except:
			BuffDict[VarId] = {}
		#print VarId,Name,ReqKnobDict[Name]
		BuffDict[VarId][len(BuffDict[VarId])] = StrVal2Hex(Var).zfill(2) + LittEndian(StrVal2Hex(Ofst).zfill(4)) + StrVal2Hex(Sz).zfill(2) + ReqValStr

	KnobBuffStr = ''
	if(len(BuffDict)):
		END_OF_BUFFER ='F4FBD0E9'
		KnobCount=0
		for Index in BuffDict:
			CurrBuffStr = ''
			for count in range (0, len(BuffDict[Index])):
				CurrBuffStr = CurrBuffStr + BuffDict[Index][count]
				KnobCount = KnobCount+1
			if(CurrBuffStr != ''):
				CurrBinBuffStr = (LittEndian(StrVal2Hex(hex(len(BuffDict[Index]))).zfill(8)) + CurrBuffStr + END_OF_BUFFER).upper()
				basepath = os.path.dirname(binfile)
				NewVarBinfile = os.sep.join([basepath, "biosKnobsdata_%d.bin" %Index])
				BIN=open(NewVarBinfile,'wb')
				BIN.writelines(binascii.unhexlify(CurrBinBuffStr))
				BIN.close()
			KnobBuffStr = KnobBuffStr + CurrBuffStr
		KnobBuffStr = (LittEndian(StrVal2Hex(hex(KnobCount)).zfill(8)) + KnobBuffStr + END_OF_BUFFER).upper()
		BIN=open(binfile,'wb')
		BIN.writelines(binascii.unhexlify(KnobBuffStr))
		BIN.close()
		#print KnobBuffStr
	return (BuffDict, KnobBuffStr)

MathOpList = {'and', 'or', 'not', '==', '!=', '<=', '>=', '<', '>', '_LIST_'}
ResultDict = {True: {'Sif': "Active", 'Gif': 'Active', 'Dif': 'Active', '': 'Active'}, False: {'Sif': "Suppressed", 'Gif': 'GrayedOut', 'Dif': 'Disabled', '': 'Unknown'}}
ListEqu = {'==': 'in', '!=':'not in'}

def MyExpEval(Depex, KnobName, KnobsValDict):
	OverallOperation = ''
	OverallResult = True
	MainExp = Depex.replace('_EQU_', '==').replace('_NEQ_', '!=').replace('_LTE_', '<=').replace('_GTE_', '>=').replace('_LT_', '<').replace('_GT_', '>').replace(' AND ', ' and ').replace(' OR ', ' or ').strip()
	ExpArray = MainExp.split('_AND_')
	for count in range (0, len(ExpArray), 1):
		Operation = ''
		if(ExpArray[count].strip() == "TRUE"):
			continue
		match = re.search(r"\s*(Sif|Gif|Dif)\s*\((.*)\)\s*", ExpArray[count])
		if (match != None):
			Operation = match.group(1).strip()
			SubExp = '( '+match.group(2).strip()+' )'
		else:
			match = re.search(r"\s*\((.*?)\)\s*", ExpArray[count])
			if (match != None):
				SubExp = '( '+match.group(1).strip()+' )'
			else:
				print "skipping this (%s) iteration" %KnobName
				continue
		# print SubExp
		for mat1 in re.finditer(r"\s*(\w+)\s", SubExp):
			Variable = mat1.group(1).strip()
			if Variable not in MathOpList:
				try:
					int(Variable, 16)
					continue
				except:
					pass
				# print '\t'+Variable
				if Variable in KnobsValDict:
					SubExp = SubExp.replace(' '+Variable+' ', ' '+KnobsValDict[Variable]['CurVal']+' ')
		match = re.search(r"\s*_LIST_\s*(.*?)\s*(==|!=)\s*(.*?)\s*(\)|or|and|not)\s*", SubExp)
		if (match != None):
			SubExp = '( '+match.group(1).strip() + ' ' + ListEqu[match.group(2).strip()] + ' [%s] )' %re.sub("\s\s*", ", ", match.group(3).strip())
		SubExp = SubExp.replace('OR', 'or')
		SubExp = SubExp.replace('AND', 'and')
		try:
			Result = eval(SubExp)
			if(Operation in ['Gif', 'Sif', 'Dif']):
				Result = not Result
		except Exception as ex:
			print ex
			Result = True
		if(Result == False):
			OverallOperation = Operation
			OverallResult = Result
			if(Operation in ['Sif', 'Dif']):
				break
	Status = ResultDict[OverallResult][OverallOperation]
	# print '\nOverall Result: Knob is %s' %Status
	return Status

def EvalKnobsDepex(PcXml=0, BiosKnobsDict=0, CsvFile=0):
	if(BiosKnobsDict == 0):
		BiosKnobsDict = {}
	BiosKnobsList={}
	if( (len(BiosKnobsDict) == 0) and (PcXml != 0) ):
		Tree = ET.parse(PcXml)
		KnobIndex = 0
		print "Parsing Xml File %s" %PcXml
		for SetupKnobs in Tree.getiterator(tag="biosknobs"):
			for BiosKnob in SetupKnobs.getchildren():
				SetupType = BiosKnob.get('setupType').strip().upper()
				KnobName = BiosKnob.get('name').strip()
				CurVal = BiosKnob.get('CurrentVal').strip()
				DefVal = BiosKnob.get('default').strip()
				Depex = "TRUE"
				SetupPgPtr = "N.A."
				Prompt = ''
				Help = ''
				OpsDict = {}
				if (SetupType in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]):
					Depex = BiosKnob.get('depex').strip()
					Prompt = BiosKnob.get('prompt').strip()
					Help = BiosKnob.get('description').strip()
					if SetupType == "ONEOF":
						OptionsCount = 0
						for options in BiosKnob.getchildren():
							for option in options.getchildren():
								OpsDict[OptionsCount] = { 'Text': nstrip(option.get("text")), 'Val': corrValue2hex(nstrip(option.get("value"))) }
								OptionsCount = OptionsCount + 1
					elif SetupType in ["NUMRIC" ,"NUMERIC"]:
						OpsDict[0] = { 'Text': 'Min', 'Val': int(corrValue2hex(nstrip(BiosKnob.get("min"))), 16) }
						OpsDict[1] = { 'Text': 'Max', 'Val': int(corrValue2hex(nstrip(BiosKnob.get("max"))), 16) }
						OpsDict[2] = { 'Text': 'Step', 'Val': int(corrValue2hex(nstrip(BiosKnob.get("step"))), 16) }
					elif (SetupType == "STRING"):
						OpsDict[0] = { 'Text': 'Min', 'Val': int(corrValue2hex(nstrip(BiosKnob.get("minsize"))), 16) }
						OpsDict[1] = { 'Text': 'Max', 'Val': int(corrValue2hex(nstrip(BiosKnob.get("maxsize"))), 16) }
						OpsDict[2] = { 'Text': 'Step', 'Val': 0x01 }
					try:
						SetupPgPtr = BiosKnob.get('SetupPgPtr').strip()
					except:
						pass
				BiosKnobsList[KnobIndex] = KnobName
				KnobIndex = KnobIndex + 1
				if(KnobName[0:4] == "Nvar"):
					TempName = KnobName[6::]
					if TempName not in BiosKnobsDict:
						BiosKnobsDict[TempName] = {'SetupType': SetupType, 'CurVal':CurVal, 'DefVal':DefVal, 'Depex':Depex, 'SetupPgPtr': SetupPgPtr, 'SetupPgSts':'Unknown', 'Prompt': Prompt, 'Help':Help, 'OptionsDict': OpsDict}
				BiosKnobsDict[KnobName] = {'SetupType': SetupType, 'CurVal':CurVal, 'DefVal':DefVal, 'Depex':Depex, 'SetupPgPtr': SetupPgPtr, 'SetupPgSts':'Unknown', 'Prompt': Prompt, 'Help':Help, 'OptionsDict': OpsDict}
	else:
		print "Skipped Parsing Xml, will directly operate & update the Knobs Dict that was passed as an Arg"

	for Knob in BiosKnobsDict:
		if(BiosKnobsDict[Knob]['SetupType'] == 'READONLY'):
			continue
		if(BiosKnobsDict[Knob]['SetupPgPtr'][0:4] == '???/'):
			BiosKnobsDict[Knob]['SetupPgSts'] = "Disabled"
		else:
			BiosKnobsDict[Knob]['SetupPgSts'] = MyExpEval(BiosKnobsDict[Knob]['Depex'], Knob, BiosKnobsDict)
	if( (CsvFile != 0) and (PcXml != 0) and (len(BiosKnobsList) != 0) ):
		MyCsvFile = open(CsvFile,'w')
		MyCsvFile.write("Name,SetupPgSts,SetupPgPtr,Depex\n")
		for Index in range (0, len(BiosKnobsList), 1):
			MyCsvFile.write("%s,%s,\"%s\",%s\n" %(BiosKnobsList[Index], BiosKnobsDict[BiosKnobsList[Index]]['SetupPgSts'], BiosKnobsDict[BiosKnobsList[Index]]['SetupPgPtr'], BiosKnobsDict[BiosKnobsList[Index]]['Depex']))
		MyCsvFile.close()
		print "generated csv file %s " %CsvFile
	return 0
