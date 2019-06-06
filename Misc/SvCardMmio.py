#-----------------------------------------------------------------------------------------------------------------------------------------
# SvMmioBios Python Library functions for What-if scenarios.
# Leverages some of the scripts and flows from ITP burn.
#
# Author:   Amol A. Shinde (amol.shinde@intel.com) & Sahil Dureja (sahil.dureja@intel.com)
# Created:  11th Nov 2013
# Modified V0.1:   11th Nov 2013 by Amol & Sahil
#
# Scope:  Intended for internal Validation use only, please dont distribute without author's consent.
#-----------------------------------------------------------------------------------------------------------------------------------------
__author__ = 'ashinde'
import itpii, os, sys
from itpii.datatypes import *
itp = itpii.baseaccess()

PCI_ENABLE_BIT     = 0x80000000
PCI_CFG_DATA       = 0xCFC
PCI_CFG_ADDR       = 0xCF8
MM_CFG_BASE        = 0x80000000
PCI_PRI_BUS_NUM    = 0x18
PCI_SEC_BUS_NUM    = 0x19
PCI_SUB_BUS_NUM    = 0x1A
PCI_NPF_MEM_BASE   = 0x20
PCI_NPF_MEM_LIMIT  = 0x22
PCI_PF_MEM_BASE    = 0x24
PCI_PF_MEM_LIMIT   = 0x26
MMIO_RULE_0        = 0x40
PCI_CMD            = 0x04
BIOS_SIZE          = 0x100000
CORIN_MMIO_SPACE   = 0x90000000
DISHON_MMIO_MB     = 0x98000000
KFIR_MMIO_SPACE    = 0xA0000000
#HIF_SHARED_MB      = (KFIR_MMIO_SPACE + 0x200000)
HIF_SHARED_MB      = DISHON_MMIO_MB
TargetGbtXmlMem    = 0x70000000
NextBus            = 1
UNCORE_BUS         = 0xFF
CORIN_PCIE_RP_DEV  = 2
DISHON_PCIE_RP_DEV = 1
KFIR_PCIE_RP_DEV   = 3

CurrPath       = os.path.abspath(os.path.dirname(__file__))
RcBinFileName  = os.sep.join([CurrPath, "rc.bin"])
RcBiosFileName = os.sep.join([CurrPath, "BiosRC.bin"])
RcBiosLog      = os.sep.join([CurrPath, "MiniBiosBoot.log"])
XmlFileName    = os.sep.join([CurrPath, "FixedPC.xml"])

def enable_sad_entries():
	"""
	enable entries for source address decoder
	"""
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	# Initialize  CPUBUSNO register in UBOX
	value = PCI_ENABLE_BIT | (1 << 16) | (16 << 11) | (0x7 << 0x8) | 0xd0
	itp.threads[0].dport(PCI_CFG_ADDR, value)
	itp.threads[0].dport(PCI_CFG_DATA, (MM_CFG_BASE + (UNCORE_BUS << 8)))

	# Initialize  MMCFG_Target_List register with all buses routed to socket 0
	value = PCI_ENABLE_BIT | (UNCORE_BUS << 16) | (0xF << 11) | (0x5 << 0x8) | 0xe4
	itp.threads[0].dport(PCI_CFG_ADDR, value)
	itp.threads[0].dport(PCI_CFG_DATA, 0x0)

	# Initialize and enable MMCFG_Rule register
	value = PCI_ENABLE_BIT | (UNCORE_BUS << 16) | (0xF << 11) | (0x5 << 0x8) | 0xC0
	itp.threads[0].dport(PCI_CFG_ADDR, value)
	# Use 0x80000000 as MMCFG base and set bit 0 to enable the rule
	itp.threads[0].dport(PCI_CFG_DATA,  (MM_CFG_BASE + 0x1))
	# init CPU_BUS_NUMBER CSR in PCU2
	# init CPUBUSNO CSR in IIO
	addr = itpii.Address(0x80028108L, itpii.AddressType.physical)
	itp.threads[0].mem(addr, 4, 0x1ff00)
	# init MMCFG CSR in IIO
	#addr = itpii.Address(0x80028084L, itpii.AddressType.physical)
	#itp.threads[0].mem(addr, 4, MM_CFG_BASE)
	#addr = itpii.Address(0x80028088L, itpii.AddressType.physical)
	#itp.threads[0].mem(addr, 4,  (MM_CFG_BASE + 0x0FFFFFFF))
	addr = itpii.Address(0x80028090L, itpii.AddressType.physical)
	itp.threads[0].mem(addr, 4, MM_CFG_BASE)
	addr = itpii.Address(0x80028098L, itpii.AddressType.physical)
	itp.threads[0].mem(addr, 4, (MM_CFG_BASE + 0x0FFFFFFF))
	print "%s() End.." %(sys._getframe().f_code.co_name)

def IoBifurcation():
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	for device in range (1, 4):
		Value = itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (device << 15) + (0 << 12) + 0x190), 4)
		itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (device << 15) + (0 << 12) + 0x190), 4, (Value|0x8))
	print "%s() End.." %(sys._getframe().f_code.co_name)

def EnableSadRule():
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	# Enable Sad Rule_0 at 1:15:5:0x40 for MMIO 
	itp.threads[0].mem( hex(MM_CFG_BASE + (UNCORE_BUS << 20) + (15 << 15) + (5 << 12) + MMIO_RULE_0), 4, 0xFB000049)
	print "%s() End.." %(sys._getframe().f_code.co_name)

def EnableCorinCard():
	global NextBus
	BusStart  = NextBus

	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, 0)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (CORIN_MMIO_SPACE >> 16 ))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, ((CORIN_MMIO_SPACE >> 16) + 0x0300))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, ((CORIN_MMIO_SPACE >> 16) + 0x0391))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (CORIN_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, ((CORIN_MMIO_SPACE >> 16) + 0x0391))

	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + 0x10), 4, CORIN_MMIO_SPACE)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + 0x1c), 4, ((CORIN_MMIO_SPACE + 0x03910000) & 0xFFF00000))
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_CMD), 1, 0x7)

	NextBus = BusStart+1
	print "Corin Card PCIE Address = 0x%X MMIO Block range = 0x%X - 0x%X " %((MM_CFG_BASE + (BusStart << 20)), CORIN_MMIO_SPACE, CORIN_MMIO_SPACE+0x10000-1)
	print "%s() End.." %(sys._getframe().f_code.co_name)
	return (CORIN_MMIO_SPACE)

def EnableDishonCard():
	global NextBus
	PF_BASE   = 0xFEF1
	PF_LIMIT  = 0xFEF1
	BusStart  = NextBus

	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, 0)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+1)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (DISHON_MMIO_MB >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, (DISHON_MMIO_MB >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (DISHON_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart+1)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+1)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (DISHON_MMIO_MB >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, (DISHON_MMIO_MB >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (0xC << 15) + (0 << 12) + 0x10), 4, (DISHON_MMIO_MB + 0x20000))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (0xC << 15) + (0 << 12) + 0x14), 4, DISHON_MMIO_MB)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (0xC << 15) + (0 << 12) + 0x18), 4, (DISHON_MMIO_MB + 0x10000))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (0xC << 15) + (0 << 12) + PCI_CMD), 1, 0x7)

	NextBus = BusStart+2
	print "Dishon Card PCIE Address = 0x%X  MMIO Block range = 0x%X - 0x%X " %((MM_CFG_BASE + ((BusStart+1) << 20) + (0xC << 15)), DISHON_MMIO_MB, DISHON_MMIO_MB+0x10000-1)
	print "%s() End.." %(sys._getframe().f_code.co_name)
	return (DISHON_MMIO_MB)

def EnableKfirCard():
	global NextBus
	PF_BASE   = 0xFFE1
	PF_LIMIT  = 0xFFE1
	BusStart  = NextBus

	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, 0)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+6)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (KFIR_MMIO_SPACE >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, ((KFIR_MMIO_SPACE >> 16) + 0x0080))
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + (0 << 20) + (KFIR_PCIE_RP_DEV << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, BusStart)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart+1)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+6)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (KFIR_MMIO_SPACE >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, ((KFIR_MMIO_SPACE >> 16) + 0x0080))
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + (BusStart << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	device = 3
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, BusStart+1)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart+4)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+5)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (KFIR_MMIO_SPACE >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, ((KFIR_MMIO_SPACE >> 16) + 0x0080))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+1) << 20) + (device << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_PRI_BUS_NUM), 1, BusStart+4)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_SEC_BUS_NUM), 1, BusStart+5)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_SUB_BUS_NUM), 1, BusStart+5)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_CMD), 1, 0x17)

	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_BASE), 2, (KFIR_MMIO_SPACE >> 16))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_NPF_MEM_LIMIT), 2, ((KFIR_MMIO_SPACE >> 16) + 0x0080))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_BASE), 2, PF_BASE)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+4) << 20) + (0 << 15) + (0 << 12) + PCI_PF_MEM_LIMIT), 2, PF_LIMIT)

	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+5) << 20) + (4 << 15) + (0 << 12) + 0x10), 4, (KFIR_MMIO_SPACE + 0x00800000))
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+5) << 20) + (4 << 15) + (0 << 12) + 0x18), 4, KFIR_MMIO_SPACE)
	itp.threads[0].mem( hex(MM_CFG_BASE + ((BusStart+5) << 20) + (4 << 15) + (0 << 12) + PCI_CMD), 1, 0x7)

	NextBus = BusStart + 7
	print "Kfir Card PCIE Address = 0x%X  MMIO Block range = 0x%X - 0x%X " %((MM_CFG_BASE + ((BusStart+5) << 20) + (4 << 15)), (KFIR_MMIO_SPACE+0x200000), KFIR_MMIO_SPACE+0x800000-1)
	print "%s() End.." %(sys._getframe().f_code.co_name)
	return (KFIR_MMIO_SPACE + 0x200000)

def EnableSvCards(LoadBios=0):
	global NextBus
	NextBus = 1
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	enable_sad_entries()
	IoBifurcation()
	EnableSadRule()
	#CorinMemBlock = EnableCorinCard()
	DishonMemBlock = EnableDishonCard()
	KfirMemblock = EnableKfirCard()
	BiosBase = KfirMemblock
	PointToCardBios(BiosBase, 0, LoadBios)
	print "%s() End.." %(sys._getframe().f_code.co_name)
	return BiosBase

def RunMmioMiniBios(DumpBiosLogs=0):
	global NextBus
	from components import ComponentManager
	sv=ComponentManager(["socket"])
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	BiosBase = EnableSvCards(LoadBios=1)
	EditGdtr(BiosBase)
	sv.refresh()
	PostCode = 0
	GbtXmlCopied = 0
	while(1):
		PostCode = (sv.socket0.uncore0.biosnonstickyscratchpad7 >> 24)
		if(GbtXmlCopied == 0):
			print "    Current BIOS Post code is 0x%X" %(PostCode)
		if( (PostCode == 0xF5) and (GbtXmlCopied == 0) ):
			#sv.socket0.uncore0.biosscratchpad6 = (0xF6 << 24)
			CopyPcXml(PostCode)
			GbtXmlCopied = 1
			print "Bios Posted 0xF5, Waiting for Loader to HandShake..."
			break
		if(PostCode == 0xF6):
			CopyPcXml(PostCode)
			#sv.socket0.uncore0.biosscratchpad6 = 0
			print "Bios operation Done, Posted 0xF6"
			break
		itp.sleep(5)
	if(DumpBiosLogs):
		DumpSerialLogs()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def MmioMiniBiosReboot(DumpBiosLogs=0):
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	DisableDmi()
	itp.sleep(30)
	RunMmioMiniBios(DumpBiosLogs)
	print "%s() End.." %(sys._getframe().f_code.co_name)

def PointToCardBios(Address, FullRcBios=0, LoadBios=1):
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.threads[0].state.regs.csbas = (Address + BIOS_SIZE - 1) & 0xFFFF0000
	itp.threads[0].state.regs.ip = 0x0000
	if(LoadBios):
		if(FullRcBios):
			RcBinFile = open(RcBinFileName, "rb")
			tmpFilePart = RcBinFile.read(0x1000000-BIOS_SIZE)
			BiosRcfilePart = RcBinFile.read(BIOS_SIZE)
			BiosRcfile = open(RcBiosFileName, "wb")
			BiosRcfile.write(BiosRcfilePart)
			BiosRcfile.close()
			RcBinFile.close()
		else:
			RcBiosFileName = os.sep.join([CurrPath, "BIOS.BIN"])
		print "loading %s file on Cards MMIO" %RcBiosFileName
		itp.threads[0].memload(RcBiosFileName, hex(Address).strip('L')+'p')
		print "Bios Code of Size 0x%X copied on Sv Card Memory 0x%X P, please proceed.." %(os.path.getsize(RcBiosFileName), Address)
	print "%s() End.." %(sys._getframe().f_code.co_name)

def EditGdtr(Address):
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.threads[0].step(steps=6)
	itp.threads[0].state.regs.gdtr = (((Address + 0xF0043) << 16) + 0x001F)
	itp.go()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def DumpSerialLogs(Filename=''):
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.halt()
	Size = int(itp.threads[0].mem(hex(KFIR_MMIO_SPACE+0x2B0000).rstrip("L")+'p', 4))
	if (Filename == ''):
		Filename = RcBiosLog
	itp.threads[0].memsave(Filename, hex(KFIR_MMIO_SPACE+0x2B0000+04).rstrip("L")+'p', Size, 1)
	itp.go()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def DisableDmi():
	from components import ComponentManager
	sv=ComponentManager(["socket"])
	sv.refresh()
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.cv.fivrbreak = 1
	itp.cv.earbreak = 1
	itp.cv.resetbreak = 1
	itp.pulsepwrgood()
	itp.wait(100)
	itp.cv.fivrbreak = 0
	itp.wait(5)
	sv.socket0.pcudata.io_reset_bypasses.start_dmi = 1
	sv.socket0.pcudata.io_reset_bypasses2.dmi_handshake = 1
	itp.cv.resetbreak = 1
	itp.cv.earbreak = 0
	itp.wait(100)
	print "We should be at Reset break with DMI disabled.."
	print "%s() End.." %(sys._getframe().f_code.co_name)

def CopyPcXml(PostCode):
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	print "Copying GBT XML from %s to Memory Address 0x%X" %(XmlFileName, TargetGbtXmlMem)
	itp.halt()
	itp.threads[0].mem(hex(HIF_SHARED_MB+0x10C).rstrip("L")+'p', 4, TargetGbtXmlMem)
	if (PostCode == 0xF5):
		XmlSize = os.path.getsize(XmlFileName)
		itp.threads[0].mem(hex(TargetGbtXmlMem+0x00).rstrip("L")+'p', 4, XmlSize)
		itp.threads[0].memload(XmlFileName, hex(TargetGbtXmlMem+0x04).rstrip("L")+'p')
		itp.msr(0x3a, 1)
		itp.threads[0].state.regs.xmm1 = TargetGbtXmlMem
	itp.go()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def FastObjCpuInit():
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.halt()
	itp.cv.initbreak = 1
	APIC_Base = (itp.threads[0].msr(0x1B) & 0xFFFFF000)
	APIC_ICR_LOW = APIC_Base + 0x300
	APIC_ICR_HIGH = APIC_Base + 0x310
	itp.threads[0].mem(hex(APIC_ICR_HIGH).rstrip("L")+'p', 4, 0x00)
	itp.threads[0].mem(hex(APIC_ICR_LOW).rstrip("L")+'p', 4, 0x500)
	itp.go()
	itp.wait(10)
	print "We are now at Init Break, updating cs:ip to point to 0x20000 P"
	itp.cv.initbreak = 0
	itp.threads[0].state.regs.ip = 0
	itp.threads[0].state.regs.cs = 0x2000
	itp.go()
	itp.wait(5)
	if ( itp.threads[0].cv.isrunning == False ):
		itp.cv.initbreak = 0
		itp.threads[0].state.regs.ip = 0
		itp.threads[0].state.regs.cs = 0x2000
		itp.go()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def CpuInit():
	print "%s() Start.." %(sys._getframe().f_code.co_name)
	itp.halt()
	itp.cv.initbreak = 1
	APIC_Base = (itp.threads[0].msr(0x1B) & 0xFFFFF000)
	APIC_ICR_LOW = APIC_Base + 0x300
	APIC_ICR_HIGH = APIC_Base + 0x310
	itp.threads[0].mem(hex(APIC_ICR_HIGH).rstrip("L")+'p', 4, 0x00)
	itp.threads[0].mem(hex(APIC_ICR_LOW).rstrip("L")+'p', 4, 0x500)
	itp.go()
	itp.wait(10)
	print "We are now at Init Break, updating cs:ip to point to 0x20000 P"
	itp.cv.initbreak = 0
	itp.threads[0].state.regs.ip = 0
	itp.threads[0].state.regs.cs = 0x2000
	itp.go()
	print "%s() End.." %(sys._getframe().f_code.co_name)

def ClearAllBrs():
	itp.cv.initbreak = 0
	itp.cv.resetbreak = 0
	itp.cv.fivrbreak = 0
	itp.cv.earbreak = 0
