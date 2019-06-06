#!/usr/bin/env python2.7
# Cscripts remove start
#-------------------------------------------------------------------------------------------------------------
# UefiFwParser.py script includes capability to parse your UEFI FW (BIOS) and can potentially fetch 
# required information from the Bios Binary.
# 
# Following are the capabilities included in this script
# 1) Parse the entire Bios region of the Bios binary by going through various Firmware Volumes and File systems
# 2) IF it finds a compressed FV in any of the file system, the script/command will decompress it and parse again
# 3) The log information of FV & FFS for the given binary will be saves at out\UefiFwPArser.log
# 4) The Script can save the desired File system referenced via its 16 byte GUID.
# 5) The GetsetBiosKnobsFromBin() function has following Capabilities,
#    - Can Parse the given Bios binary and fetch required File systems to gather Bios knobs information.
#    - Gets the BIOS ID string embedded/encoded in Bios binary.
#    - Parses the HII DB & NVRAM section in the Bios binary and generates a complete Bios Knobs 
#      information in XML file format
#    - Provides an ability to update Bios Knobs default values and generates corresponding 
#      Bios Binary with desired Default settings.
# 6) Flexcon can easily import this capability and potentially have the capability to operate on 
#    Bios binaries to update default Values of knobs for the given Binary
# 7) Since this script operates on Bios Binary file, it doesnt need a SUT to run on.
#
# Author:   Amol A. Shinde (amol.shinde@intel.com)
# Created:  7th Aug 2014
# Modified V0.1:   8th Aug 2014 by Amol
# Modified V0.2:   10th Aug 2014 by Amol
# Modified V0.3:   12th Aug 2014 by Amol
# Modified V0.4:   13th August 2014 by Amol
# Modified V0.5:   18th August 2014 by Amol
# Modified V0.6:   4th December 2014 by Amol Add Firmware ingredient details to the XML.
# Modified V0.7:   5th March 2015 by Amol, Added support for Setup Page ptr for BiosKnobs in Offline binary parsing
__author__ = 'ashinde'
# Cscripts remove end
import sys, os, binascii, string, time, filecmp, glob, re
import XmlIniParser as prs
import XmlCliLib as clb

FvMainFileName = clb.TempFolder+os.sep+"FvMain_0.fv"

global LogEnabled, FileGuidListDict, FileSystemSaveCount, FwIngrediantDict, BiosKnobDict, HiiNvarDict

FwIngrediantDict = {}
FwIngrediantDict['FlashDescpValid'] = 0
FwIngrediantDict['FitTablePtr'] = 0
FwIngrediantDict['FlashRegions'] = {}
FwIngrediantDict['PCH_STRAPS'] = {}
FwIngrediantDict['ME'] = {}
FwIngrediantDict['FIT'] = {}
FwIngrediantDict['ACM'] = {}
FwIngrediantDict['Ucode'] = {}
FwpLogEn = True
FwpPrintEn = False
FileGuidListDict = {}
FileSystemSaveCount = 0
FvMainCompDict = {}
SaveFvMainFile = False
FvMainCount = 0
Parse_Print_Uqi = False
PlatInfoMenuDone = False
ForceOutFile = False

EFI_GUID_DEFINED_SECTION_HDR_SIZE = 0x18
FFS_FILE_HEADER_SIZE              = 0x18
FFS_FILE_HEADER2_SIZE             = 0x20
FFS_ATTRIB_LARGE_FILE             = 0x01
EFI_COMMON_SECTION_HEADER_SIZE    = 0x04
FV_FILETYPE_FIRMWARE_VOLUME_IMAGE = 0x0B
EFI_FV_HEADER_SIZE                = 0x48
EFI_SECTION_GUID_DEFINED          = 0x02

# FFS File Attributes.
FFS_ATTRIB_FIXED                  = 0x04
FFS_ATTRIB_DATA_ALIGNMENT         = 0x38
FFS_ATTRIB_CHECKSUM               = 0x40

# FFS_FIXED_CHECKSUM is the checksum value used when the FFS_ATTRIB_CHECKSUM attribute bit is clear
FFS_FIXED_CHECKSUM                = 0xAA

EFI_IFR_FORM_SET_OP               = 0x0E
EFI_IFR_FORM_OP                   = 0x01
EFI_IFR_SUBTITLE_OP               = 0x02
EFI_IFR_TEXT_OP                   = 0x03
EFI_IFR_SUPPRESS_IF_OP            = 0x0A
EFI_IFR_GRAY_OUT_IF_OP            = 0x19
EFI_IFR_REF_OP                    = 0x0F
EFI_IFR_VARSTORE_OP               = 0x24
EFI_IFR_VARSTORE_EFI_OP           = 0x26
EFI_IFR_ONE_OF_OP                 = 0x05
EFI_IFR_CHECKBOX_OP               = 0x06
EFI_IFR_NUMERIC_OP                = 0x07
EFI_IFR_ONE_OF_OPTION_OP          = 0x09
EFI_IFR_STRING_OP                 = 0x1C
EFI_HII_PACKAGE_FORMS             = 0x02
EFI_HII_PACKAGE_STRINGS           = 0x04
EFI_IFR_NUMERIC_SIZE              = 0x03
EFI_IFR_END_OP                    = 0x29
EFI_IFR_TRUE_OP                   = 0x46
EFI_IFR_DEFAULT_OP                = 0x5B
EFI_IFR_GUID_OP                   = 0x5F

EFI_HII_SIBT_END                  = 0x00
EFI_HII_SIBT_STRING_SCSU          = 0x10
EFI_HII_SIBT_STRING_SCSU_FONT     = 0x11
EFI_HII_SIBT_STRINGS_SCSU         = 0x12
EFI_HII_SIBT_STRINGS_SCSU_FONT    = 0x13
EFI_HII_SIBT_STRING_UCS2          = 0x14
EFI_HII_SIBT_STRING_UCS2_FONT     = 0x15
EFI_HII_SIBT_STRINGS_UCS2         = 0x16
EFI_HII_SIBT_STRINGS_UCS2_FONT    = 0x17
EFI_HII_SIBT_DUPLICATE            = 0x20
EFI_HII_SIBT_SKIP2                = 0x21
EFI_HII_SIBT_SKIP1                = 0x22
EFI_HII_SIBT_EXT1                 = 0x30
EFI_HII_SIBT_EXT2                 = 0x31
EFI_HII_SIBT_EXT4                 = 0x32
EFI_HII_SIBT_FONT                 = 0x40

EFI_IFR_TYPE_NUM_SIZE_8           = 0x00
EFI_IFR_TYPE_NUM_SIZE_16          = 0x01
EFI_IFR_TYPE_NUM_SIZE_32          = 0x02
EFI_IFR_TYPE_NUM_SIZE_64          = 0x03
EFI_IFR_TYPE_BOOLEAN              = 0x04

EFI_IFR_OPTION_DEFAULT            = 0x10
EFI_IFR_OPTION_DEFAULT_MFG        = 0x20

BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD  = 0x10
INVALID_KNOB_SIZE                 = 0xFF
BIOS_KNOBS_DATA_BIN_HDR_SIZE      = 0x40
BIOS_KNOBS_DATA_BIN_HDR_SIZE_V03  = 0x50
BIOS_KNOB_BIN_REVISION_OFFSET     = 0x0F
NVAR_NAME_OFFSET                  = 0x0E
BIOS_KNOB_BIN_GUID_OFFSET         = 0x12

Descriptor_Region                 = 0
BIOS_Region                       = 1
ME_Region                         = 2
GBE_Region                        = 3
PDR_Region                        = 4
Device_Expan_Region               = 5
Sec_BIOS_Region                   = 6
SpiRegionAll                      = 6
SpiRegionMax                      = 7
Invalid_Region                    = 0xFF
FlashRegionDict                   = {Descriptor_Region: 'Descriptor', BIOS_Region: 'BIOS', ME_Region: 'ME', GBE_Region: 'GBE', PDR_Region: 'PDR', Device_Expan_Region: 'Device Expansion', Sec_BIOS_Region: 'Secondary BIOS'}

gEfiFirmwareFileSystemGuid        = [ 0x7A9354D9, 0x0468, 0x444a, 0x81, 0xCE, 0x0B, 0xF6, 0x17, 0xD8, 0x90, 0xDF ]
gEfiFirmwareFileSystem2Guid       = [ 0x8c8ce578, 0x8a3d, 0x4f1c, 0x99, 0x35, 0x89, 0x61, 0x85, 0xc3, 0x2d, 0xd3 ]
gEfiFirmwareFileSystem3Guid       = [ 0x5473c07a, 0x3dcb, 0x4dca, 0xbd, 0x6f, 0x1e, 0x96, 0x89, 0xe7, 0x34, 0x9a ]

gEfiGlobalVariableGuid            = [ 0x8BE4DF61, 0x93CA, 0x11D2, 0xAA, 0x0D, 0x00, 0xE0, 0x98, 0x03, 0x2B, 0x8C ]
gEfiVariableGuid                  = [ 0xddcf3616, 0x3275, 0x4164, 0x98, 0xb6, 0xfe, 0x85, 0x70, 0x7f, 0xfe, 0x7d ]
gEfiIfrTianoGuid                  = [ 0x0f0b1735, 0x87a0, 0x4193, 0xb2, 0x66, 0x53, 0x8c, 0x38, 0xaf, 0x48, 0xce ]
gEfiAuthenticatedVariableGuid     = [ 0xaaf32c78, 0x947b, 0x439a, 0xa1, 0x80, 0x2e, 0x14, 0x4e, 0xc3, 0x77, 0x92 ]
gTianoCustomDecompressGuid        = [ 0xA31280AD, 0x481E, 0x41B6, 0x95, 0xE8, 0x12, 0x7F, 0x4C, 0x98, 0x47, 0x79 ]
gLzmaCustomDecompressGuid         = [ 0xEE4E5898, 0x3914, 0x4259, 0x9D, 0x6E, 0xDC, 0x7B, 0xD7, 0x94, 0x03, 0xCF ]
gBrotliCustomDecompressGuid       = [ 0x3D532050, 0x5CDA, 0x4FD0, 0x87, 0x9E, 0x0F, 0x7F, 0x63, 0x0D, 0x5A, 0xFB ]
gNvRamFvGuid                      = [ 0xFFF12B8D, 0x7696, 0x4c8b, 0xa9, 0x85, 0x27, 0x47, 0x07, 0x5b, 0x4f, 0x50 ]
gEfiFirmwareContentsSignedGuid    = [ 0x0f9d89e8, 0x9259, 0x4f76, 0xa5, 0xaf, 0xc,  0x89, 0xe3, 0x40, 0x23, 0xdf ]
gEfiCertTypeRsa2048Sha256Guid     = [ 0xa7717414, 0xc616, 0x4977, 0x94, 0x20, 0x84, 0x47, 0x12, 0xa7, 0x35, 0xbf ]
gEfiHashAlgorithmSha256Guid       = [ 0x51AA59DE, 0xFDF2, 0x4EA3, 0xBC, 0x63, 0x87, 0x5F, 0xB7, 0x84, 0x2E, 0xE9 ]

gBiosCapsuleGuid                  = [ 0xda4b2d79, 0xfee1, 0x42c6, 0x9b, 0x56, 0x92, 0x36, 0x33, 0x39, 0x8a, 0xeb ]

gBiosKnobsDataBinGuid             = [ 0x615E6021, 0x603D, 0x4124, 0xB7, 0xEA, 0xC4, 0x8A, 0x37, 0x37, 0xBA, 0xCD ]
gXmlCliProtocolGuid               = [ 0xe3e49b8d, 0x1987, 0x48d0, 0x9a, 0x1,  0xed, 0xa1, 0x79, 0xca, 0xb,  0xd6 ]

gDxePlatformFfsGuid               = [ 0xABBCE13D, 0xE25A, 0x4d9f, 0xA1, 0xF9, 0x2F, 0x77, 0x10, 0x78, 0x68, 0x92 ]
gAdvancedPkgListGuid              = [ 0xc09c81cb, 0x31e9, 0x4de6, 0xa9, 0xf9, 0x17, 0xa1, 0x44, 0x35, 0x42, 0x45 ]

gSocketSetupDriverFfsGuid         = [ 0x6B6FD380, 0x2C55, 0x42C6, 0x98, 0xBF, 0xCB, 0xBC, 0x5A, 0x9A, 0xA6, 0x66 ]
gSocketPkgListGuid                = [ 0x5c0083db, 0x3f7d, 0x4b20, 0xac, 0x9b, 0x73, 0xfc, 0x65, 0x1b, 0x25, 0x03 ]

gSvSetupDriverFfsGuid             = [ 0x5498AB03, 0x63AE, 0x41A5, 0xB4, 0x90, 0x29, 0x94, 0xE2, 0xDA, 0xC6, 0x8D ]
gSvPkgListGuid                    = [ 0xaec3ff43, 0xa70f, 0x4e01, 0xa3, 0x4b, 0xee, 0x1d, 0x11, 0xaa, 0x21, 0x69 ]

gFpgaDriverFfsGuid                = [ 0xBCEA6548, 0xE204, 0x4486, 0x8F, 0x2A, 0x36, 0xE1, 0x3C, 0x78, 0x38, 0xCE ]
gFpgaPkgListGuid                  = [ 0x22819110, 0x7f6f, 0x4852, 0xb4, 0xbb, 0x13, 0xa7, 0x70, 0x14, 0x9b, 0x0c ]

gPcGenSetupDriverFfsGuid          = [ 0xCB105C8B, 0x3B1F, 0x4117, 0x99, 0x3B, 0x6D, 0x18, 0x93, 0x39, 0x37, 0x16 ]

gClientSetupFfsGuid               = [ 0xE6A7A1CE, 0x5881, 0x4b49, 0x80, 0xBE, 0x69, 0xC9, 0x18, 0x11, 0x68, 0x5C ]
gClientTestMenuSetupFfsGuid       = [ 0x21535212, 0x83d1, 0x4d4a, 0xae, 0x58, 0x12, 0xf8, 0x4d, 0x1f, 0x71, 0x0d ]
gDefaultDataOptSizeFileGuid       = [ 0x003e7b41, 0x98a2, 0x4be2, 0xb2, 0x7a, 0x6c, 0x30, 0xc7, 0x65, 0x52, 0x25 ]
gDefaultDataFileGuid              = [ 0x1ae42876, 0x008f, 0x4161, 0xb2, 0xb7, 0x1c, 0xd,  0x15, 0xc5, 0xef, 0x43 ]
gVpdGuid                          = [ 0x8C3D856A, 0x9BE6, 0x468E, 0x85, 0x0A, 0x24, 0xF7, 0xA8, 0xD3, 0x8E, 0x08 ]

gEfiSetupVariableGuid             = [ 0xec87d643, 0xeba4, 0x4bb5, 0xa1, 0xe5, 0x3f, 0x3e, 0x36, 0xb2, 0x0d, 0xa9 ]
gEfiBiosIdGuid                    = [ 0xC3E36D09, 0x8294, 0x4b97, 0xA8, 0x57, 0xD5, 0x28, 0x8F, 0xE3, 0x3E, 0x28 ]
gCpPcBiosIdFileGuid               = [ 0x372f8c51, 0xc43b, 0x472a, 0x82, 0xaf, 0x54, 0xb5, 0xc3, 0x23, 0x4d, 0x7f ]

gEmulationDriverFfsGuid           = [ 0x6BB0C4DE, 0xDCA4, 0x4f3e, 0xBC, 0xA8, 0x33, 0x06, 0x35, 0xDA, 0x4E, 0xF3 ]
gEmulatioPkgListGuid              = [ 0x52b3b56e, 0xe716, 0x455f, 0xa5, 0xe3, 0xb3, 0x14, 0xf1, 0x8e, 0x6c, 0x5d ]

gMerlinXAppGuid                   = [ 0xA3D1DDB4, 0xADB2, 0x4a08, 0xA0, 0x38, 0x73, 0x05, 0x67, 0x30, 0xE8, 0x53 ]

ZeroGuid                          = [ 0x00000000, 0x0000, 0x0000, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ]
AllFsGuid                         = [ 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]

FFSfileTypesDict     = { 0x00 : "FV_FILETYPE_ALL", 0x01 : "FV_FILETYPE_RAW", 0x02 : "FV_FILETYPE_FREEFORM", 0x03 : "FV_FILETYPE_SECURITY_CORE", 0x04 : "FV_FILETYPE_PEI_CORE", 0x05 : "FV_FILETYPE_DXE_CORE", 0x06 : "FV_FILETYPE_PEIM", 0x07 : "FV_FILETYPE_DRIVER", 0x08 : "FV_FILETYPE_COMBINED_PEIM_DRIVER", 0x09 : "FV_FILETYPE_APPLICATION", 0x0A : "FV_FILETYPE_SMM", 0x0B : "FV_FILETYPE_FIRMWARE_VOLUME_IMAGE", 0x0C : "FV_FILETYPE_COMBINED_SMM_DXE", 0x0D : "FV_FILETYPE_SMM_CORE", 0xC0 : "FV_FILETYPE_OEM_MIN", 0xDF : "FV_FILETYPE_OEM_MAX", 0xE0 : "FV_FILETYPE_DEBUG_MIN", 0xEF : "FV_FILETYPE_DEBUG_MAX", 0xFF : "FV_FILETYPE_FFS_MAX", 0xF0 : "FV_FILETYPE_FFS_PAD" }
FFSsectionTypeDict   = { 0x00 : "EFI_SECTION_ALL", 0x01 : "EFI_SECTION_COMPRESSION", 0x02 : "EFI_SECTION_GUID_DEFINED", 0x10 : "EFI_SECTION_PE32", 0x11 : "EFI_SECTION_PIC", 0x12 : "EFI_SECTION_TE", 0x13 : "EFI_SECTION_DXE_DEPEX", 0x14 : "EFI_SECTION_VERSION", 0x15 : "EFI_SECTION_USER_INTERFACE", 0x16 : "EFI_SECTION_COMPATIBILITY16", 0x17 : "EFI_SECTION_FIRMWARE_VOLUME_IMAGE", 0x18 : "EFI_SECTION_FREEFORM_SUBTYPE_GUID", 0x19 : "EFI_SECTION_RAW", 0x1B : "EFI_SECTION_PEI_DEPEX", 0x1C : "EFI_SECTION_SMM_DEPEX" }
GuidedSectAtrbDict   = { 0x01 : "EFI_GUIDED_SECTION_PROCESSING_REQUIRED", 0x02 : "EFI_GUIDED_SECTION_AUTH_STATUS_VALID" }
HiiPkgHdrTypeDict    = { 0x00 : "EFI_HII_PACKAGE_TYPE_ALL", 0x01 : "EFI_HII_PACKAGE_TYPE_GUID", 0x02 : "EFI_HII_PACKAGE_FORMS", 0x04 : "EFI_HII_PACKAGE_STRINGS", 0x05 : "EFI_HII_PACKAGE_FONTS", 0x06 : "EFI_HII_PACKAGE_IMAGES", 0x07 : "EFI_HII_PACKAGE_SIMPLE_FONTS", 0x08 : "EFI_HII_PACKAGE_DEVICE_PATH", 0x09 : "EFI_HII_PACKAGE_KEYBOARD_LAYOUT", 0x0A : "EFI_HII_PACKAGE_ANIMATIONS", 0xDF : "EFI_HII_PACKAGE_END", 0xE0 : "EFI_HII_PACKAGE_TYPE_SYSTEM_BEGIN", 0xFF : "EFI_HII_PACKAGE_TYPE_SYSTEM_END" }
IfrOpcodesDict       = { 0x01 : "EFI_IFR_FORM_OP", 0x02 : "EFI_IFR_SUBTITLE_OP", 0x03 : "EFI_IFR_TEXT_OP", 0x04 : "EFI_IFR_IMAGE_OP", 0x05 : "EFI_IFR_ONE_OF_OP", 0x06 : "EFI_IFR_CHECKBOX_OP", 0x07 : "EFI_IFR_NUMERIC_OP", 0x08 : "EFI_IFR_PASSWORD_OP", 0x09 : "EFI_IFR_ONE_OF_OPTION_OP", 0x0A : "EFI_IFR_SUPPRESS_IF_OP", 0x0B : "EFI_IFR_LOCKED_OP", 0x0C : "EFI_IFR_ACTION_OP", 0x0D : "EFI_IFR_RESET_BUTTON_OP", 0x0E : "EFI_IFR_FORM_SET_OP", 0x0F : "EFI_IFR_REF_OP", 0x10 : "EFI_IFR_NO_SUBMIT_IF_OP", 0x11 : "EFI_IFR_INCONSISTENT_IF_OP", 0x12 : "EFI_IFR_EQ_ID_VAL_OP", 0x13 : "EFI_IFR_EQ_ID_ID_OP", 0x14 : "EFI_IFR_EQ_ID_VAL_LIST_OP", 0x15 : "EFI_IFR_AND_OP", 0x16 : "EFI_IFR_OR_OP", 0x17 : "EFI_IFR_NOT_OP", 0x18 : "EFI_IFR_RULE_OP", 0x19 : "EFI_IFR_GRAY_OUT_IF_OP", 0x1A : "EFI_IFR_DATE_OP", 0x1B : "EFI_IFR_TIME_OP", 0x1C : "EFI_IFR_STRING_OP", 0x1D : "EFI_IFR_REFRESH_OP", 0x1E : "EFI_IFR_DISABLE_IF_OP", 0x1F : "EFI_IFR_ANIMATION_OP", 0x20 : "EFI_IFR_TO_LOWER_OP", 0x21 : "EFI_IFR_TO_UPPER_OP", 0x22 : "EFI_IFR_MAP_OP", 0x23 : "EFI_IFR_ORDERED_LIST_OP", 0x24 : "EFI_IFR_VARSTORE_OP", 0x25 : "EFI_IFR_VARSTORE_NAME_VALUE_OP", 0x26 : "EFI_IFR_VARSTORE_EFI_OP", 0x27 : "EFI_IFR_VARSTORE_DEVICE_OP", 0x28 : "EFI_IFR_VERSION_OP", 0x29 : "EFI_IFR_END_OP", 0x2A : "EFI_IFR_MATCH_OP", 0x2B : "EFI_IFR_GET_OP", 0x2C : "EFI_IFR_SET_OP", 0x2D : "EFI_IFR_READ_OP", 0x2E : "EFI_IFR_WRITE_OP", 0x2F : "EFI_IFR_EQUAL_OP", 0x30 : "EFI_IFR_NOT_EQUAL_OP", 0x31 : "EFI_IFR_GREATER_THAN_OP", 0x32 : "EFI_IFR_GREATER_EQUAL_OP", 0x33 : "EFI_IFR_LESS_THAN_OP", 0x34 : "EFI_IFR_LESS_EQUAL_OP", 0x35 : "EFI_IFR_BITWISE_AND_OP", 0x36 : "EFI_IFR_BITWISE_OR_OP", 0x37 : "EFI_IFR_BITWISE_NOT_OP", 0x38 : "EFI_IFR_SHIFT_LEFT_OP", 0x39 : "EFI_IFR_SHIFT_RIGHT_OP", 0x3A : "EFI_IFR_ADD_OP", 0x3B : "EFI_IFR_SUBTRACT_OP", 0x3C : "EFI_IFR_MULTIPLY_OP", 0x3D : "EFI_IFR_DIVIDE_OP", 0x3E : "EFI_IFR_MODULO_OP", 0x3F : "EFI_IFR_RULE_REF_OP", 0x40 : "EFI_IFR_QUESTION_REF1_OP", 0x41 : "EFI_IFR_QUESTION_REF2_OP", 0x42 : "EFI_IFR_UINT8_OP", 0x43 : "EFI_IFR_UINT16_OP", 0x44 : "EFI_IFR_UINT32_OP", 0x45 : "EFI_IFR_UINT64_OP", 0x46 : "EFI_IFR_TRUE_OP", 0x47 : "EFI_IFR_FALSE_OP", 0x48 : "EFI_IFR_TO_UINT_OP", 0x49 : "EFI_IFR_TO_STRING_OP", 0x4A : "EFI_IFR_TO_BOOLEAN_OP", 0x4B : "EFI_IFR_MID_OP", 0x4C : "EFI_IFR_FIND_OP", 0x4D : "EFI_IFR_TOKEN_OP", 0x4E : "EFI_IFR_STRING_REF1_OP", 0x4F : "EFI_IFR_STRING_REF2_OP", 0x50 : "EFI_IFR_CONDITIONAL_OP", 0x51 : "EFI_IFR_QUESTION_REF3_OP", 0x52 : "EFI_IFR_ZERO_OP", 0x53 : "EFI_IFR_ONE_OP", 0x54 : "EFI_IFR_ONES_OP", 0x55 : "EFI_IFR_UNDEFINED_OP", 0x56 : "EFI_IFR_LENGTH_OP", 0x57 : "EFI_IFR_DUP_OP", 0x58 : "EFI_IFR_THIS_OP", 0x59 : "EFI_IFR_SPAN_OP", 0x5A : "EFI_IFR_VALUE_OP", 0x5B : "EFI_IFR_DEFAULT_OP", 0x5C : "EFI_IFR_DEFAULTSTORE_OP", 0x5D : "EFI_IFR_FORM_MAP_OP", 0x5E : "EFI_IFR_CATENATE_OP", 0x5F : "EFI_IFR_GUID_OP", 0x60 : "EFI_IFR_SECURITY_OP", 0x61 : "EFI_IFR_MODAL_TAG_OP", 0x62 : "EFI_IFR_REFRESH_ID_OP", 0x63 : "EFI_IFR_WARNING_IF_OP" }
SetupTypeHiiDict     = { EFI_IFR_ONE_OF_OP:'oneof', EFI_IFR_NUMERIC_OP:'numeric', EFI_IFR_CHECKBOX_OP:'checkbox', EFI_IFR_STRING_OP:'string' }
SetupTypeBinDict     = { 0x5:'oneof', 0x7:'numeric', 0x6:'checkbox', 0x8:'string' }
SetupTypeBin2ValDict = { 0x5:EFI_IFR_ONE_OF_OP, 0x7:EFI_IFR_NUMERIC_OP, 0x6:EFI_IFR_CHECKBOX_OP, 0x8:EFI_IFR_STRING_OP }

PrintLogFile = clb.TempFolder+os.sep+"UefiFwParser.log"
TabLevel = 0

def ReadList(buffer, offset, size):
	return int(binascii.hexlify(string.join(buffer[offset:offset+size][::-1], '')), 16)

def WriteList(buffer, offset, size, Value):
	for count in range (0, size):
		buffer[offset+count] = chr((Value >> (count*8)) & 0xFF)

def PrintLog(String, LogFile):
	global TabLevel
	if(FwpLogEn or FwpPrintEn):
		Tab = ""
		for count in range (0, TabLevel):
			Tab = Tab + "   |"
		String = '|' + Tab + String
		if(FwpPrintEn):
			print "%s" %String
		if ( (LogFile != 0) and FwpLogEn ):
			LogFile.write(String+'\n')

def GuidStr(GuidList):
	GuidString = "{ 0x%08X, 0x%04X, 0x%04X, { 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X, 0x%02X }}" %(GuidList[0], GuidList[1], GuidList[2], GuidList[3], GuidList[4], GuidList[5], GuidList[6], GuidList[7], GuidList[8], GuidList[9], GuidList[10])
	return GuidString

def FetchGuid(BufferList, Offset):
	GuidList = []
	if (len(BufferList) > (Offset + 0x10)):
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0x0):(Offset+0x4)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0x4):(Offset+0x6)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0x6):(Offset+0x8)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0x8):(Offset+0x9)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0x9):(Offset+0xA)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xA):(Offset+0xB)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xB):(Offset+0xC)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xC):(Offset+0xD)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xD):(Offset+0xE)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xE):(Offset+0xF)][::-1], '')), 16))
			GuidList.append(int(binascii.hexlify(string.join(BufferList[(Offset+0xF):(Offset+0x10)][::-1], '')), 16))
	else:
			GuidList = ZeroGuid
	return GuidList

def DelTempFvFfsFiles(Folder):
	DelFileTypes = ["*.fv", "*.ffs", "*.sec", "*.guided", "*.tmp"]
	for FileType in DelFileTypes:
		TempFvFileList = glob.glob(os.sep.join([Folder, FileType]))
		for TempFile in TempFvFileList:
			clb.RemoveFile(TempFile)

#    #define EFI_FVH_SIGNATURE EFI_SIGNATURE_32 ('_', 'F', 'V', 'H')
#    // Describes the features and layout of the firmware volume.
#    typedef struct {
#      UINT8                     ZeroVector[16];
#      EFI_GUID                  FileSystemGuid;
#      UINT64                    FvLength;
#      UINT32                    Signature;
#      EFI_FVB_ATTRIBUTES_2      Attributes;
#      UINT16                    HeaderLength;
#      UINT16                    Checksum;
#      UINT16                    ExtHeaderOffset;
#      UINT8                     Reserved[1];
#      UINT8                     Revision;
#      EFI_FV_BLOCK_MAP_ENTRY    BlockMap[1];
#    } EFI_FIRMWARE_VOLUME_HEADER;
#
#    typedef UINT8 EFI_FV_FILETYPE;
#    typedef UINT8 EFI_FFS_FILE_ATTRIBUTES;
#    typedef UINT8 EFI_FFS_FILE_STATE;
#
#    typedef union {
#      struct {
#        UINT8   Header;
#        UINT8   File;
#      } Checksum;
#      UINT16    Checksum16;
#    } EFI_FFS_INTEGRITY_CHECK;
#
#    typedef struct {
#      EFI_GUID                  Name;
#      EFI_FFS_INTEGRITY_CHECK   IntegrityCheck;
#      EFI_FV_FILETYPE           Type;
#      EFI_FFS_FILE_ATTRIBUTES   Attributes;
#      UINT8                     Size[3];
#      EFI_FFS_FILE_STATE        State;
#    } EFI_FFS_FILE_HEADER;
#
#    typedef struct {
#      EFI_GUID                Name;
#      EFI_FFS_INTEGRITY_CHECK IntegrityCheck;
#      EFI_FV_FILETYPE         Type;
#      EFI_FFS_FILE_ATTRIBUTES Attributes;
#      UINT8                   Size[3];
#      EFI_FFS_FILE_STATE      State;
#      UINT32                  ExtendedSize;
#    } EFI_FFS_FILE_HEADER2;
#
#    typedef UINT8 EFI_SECTION_TYPE;
#    typedef struct {
#      UINT8             Size[3];
#      EFI_SECTION_TYPE  Type;
#    } EFI_COMMON_SECTION_HEADER;
#
#    typedef struct {
#      EFI_COMMON_SECTION_HEADER   CommonHeader;
#      EFI_GUID                    SubTypeGuid;
#    } EFI_FREEFORM_SUBTYPE_GUID_SECTION;
#
#
#    # Leaf section which is encapsulation defined by specific GUID
#    typedef struct {
#      EFI_COMMON_SECTION_HEADER   CommonHeader;
#      EFI_GUID                    SectionDefinitionGuid;
#      UINT16                      DataOffset;
#      UINT16                      Attributes;
#    } EFI_GUID_DEFINED_SECTION;

def ProcessBin(BiosBinListBuff=[], BiosFvBase=0x800000, Files2saveGuidList=[], LogFile=0, SkipGuidedSec=False, IsCmprFv=False, BiosRegionEnd=0):
	global TabLevel, FileGuidListDict, FileSystemSaveCount, FvMainCompDict, SaveFvMainFile, FvMainCount

	if(BiosRegionEnd == 0):
		BiosRegionEnd = len(BiosBinListBuff)
	PrintLog("-----------------------------------------------------------------------------------------------------", LogFile)
	HeaderGuid = FetchGuid(BiosBinListBuff, BiosFvBase)
	if(HeaderGuid == gBiosCapsuleGuid):
		BiosFvBase = BiosFvBase + ReadList(BiosBinListBuff, (BiosFvBase + 0x10), 4)
	for FvCount in range (0, 8000):
		if (BiosFvBase >= BiosRegionEnd):
			break
		FvZeroVect  = FetchGuid(BiosBinListBuff, BiosFvBase)
		FvGuid  = FetchGuid(BiosBinListBuff, (BiosFvBase + 0x10))
		if( (FvZeroVect == ZeroGuid) and (FvGuid != ZeroGuid) ):		# Every valid FV needs to have this zero vector. 
			FvSize = ReadList(BiosBinListBuff, (BiosFvBase + 0x20), 8)
			if ( (FvGuid == AllFsGuid) and (FvSize == 0xFFFFFFFFFFFFFFFF) ):
				BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)
				continue	# InValid FV, skip this iteration
			if(FvGuid == gEfiFirmwareFileSystemGuid):
				FileSystemTypeFound = 1
			elif(FvGuid == gEfiFirmwareFileSystem2Guid):
				FileSystemTypeFound = 2
			elif(FvGuid == gEfiFirmwareFileSystem3Guid):
				FileSystemTypeFound = 3
			else:
				FileSystemTypeFound = 0
			FvSignature = ReadList(BiosBinListBuff, (BiosFvBase + 0x28), 4)
			if (FvSignature!=0x4856465F): #"_FVH" = 0x4856465F
				BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)
				continue # InValid FV, skip this iteration
			FvHdrLen = ReadList(BiosBinListBuff, (BiosFvBase + 0x30), 2)
			FVChecksum = ReadList(BiosBinListBuff, (BiosFvBase + 0x32), 2)
			ExtHdrOffset = ReadList(BiosBinListBuff, (BiosFvBase + 0x34), 2)
			FvRev = ReadList(BiosBinListBuff, (BiosFvBase + 0x37), 1)
			FvBlocks = ReadList(BiosBinListBuff, (BiosFvBase + 0x38), 4)
			BlockLen = ReadList(BiosBinListBuff, (BiosFvBase + 0x3C), 4)
			if(ExtHdrOffset):
				FvNameGuid = FetchGuid(BiosBinListBuff, (BiosFvBase+ExtHdrOffset))
				ExtHdrSize = ReadList(BiosBinListBuff, (BiosFvBase+ExtHdrOffset+0x10), 4)
				FvHdrLen = ExtHdrOffset + ExtHdrSize
			PrintLog(" BiosFvBase = 0x%08X FvSize : 0x%X FvSignature = \"%s\" FvHdrLen = 0x%X ExtHdrOfst = 0x%X" %(BiosFvBase, FvSize, binascii.unhexlify(hex(FvSignature)[2:])[::-1], FvHdrLen, ExtHdrOffset), LogFile)
			if(ExtHdrOffset):
				PrintLog(" FvNameGuid = %s" %GuidStr(FvNameGuid), LogFile)
			PrintLog(" FVChecksum = 0x%X  FvRev = 0x%X  NoOfBlocks = 0x%X  BlockLen = 0x%X  FileSystemType = %d" %(FVChecksum, FvRev, FvBlocks, BlockLen, FileSystemTypeFound), LogFile)
			PrintLog(" FvGuid : %s " %GuidStr(FvGuid), LogFile)
			BiosFFsbase = BiosFvBase+FvHdrLen
			FileSystembase = (BiosFFsbase + 7 ) & 0xFFFFFFF8		# this is because FileSystem sits on a 8 byte boundary
			if (FileSystembase >= (BiosFvBase + FvSize)):
				TabLevel = TabLevel - 1
				PrintLog("-------------------------------------------------------------------------------------", LogFile)
				BiosFvBase = (BiosFvBase + FvSize)
				continue
			FirstFsGuid = FetchGuid(BiosBinListBuff, FileSystembase)
			if ( FirstFsGuid != AllFsGuid ):
				for FileGuid in Files2saveGuidList:
					if ( FvGuid == FileGuid ):
						FvFileName = clb.TempFolder+os.sep+"%X_File.fv" %FvGuid[0]
						PrintLog(" ++++++++++   Saving FV file as %s   ++++++++++   |" %FvFileName, LogFile)
						FfsFile = open(FvFileName, 'wb')
						FfsFile.write(string.join(BiosBinListBuff[BiosFvBase:BiosFvBase+FvSize], ''))
						FfsFile.close()
						FileGuidListDict[FileSystemSaveCount] = {'FileGuid':FileGuid, 'BiosBinPointer':BiosFvBase, 'FileSystemSize':FvSize, 'IsCmprFv': IsCmprFv, 'FvMainCount': FvMainCount}
						FileSystemSaveCount = FileSystemSaveCount + 1
						if(FileSystemSaveCount >= len(Files2saveGuidList)):
							TabLevel = 0
							return
						break
			TabLevel = TabLevel + 1
			PrintLog("-------------------------------------------------------------------------------------", LogFile)
			for FfsCount in range (0, 8000):
				if(FileSystemTypeFound == 0):
					PrintLog(" Unknown FileSystem, skipping File System Parsing for current FV....", LogFile)
					break
				BiosFFsbase = (BiosFFsbase + 7 ) & 0xFFFFFFF8		# this is because FFS sits on a 8 byte boundary
				if (BiosFFsbase >= (BiosFvBase + FvSize)):
					break
				FFsGuid = FetchGuid(BiosBinListBuff, BiosFFsbase)
				if ( FFsGuid == ZeroGuid ):
					break
				FFShdrChksm = ReadList(BiosBinListBuff, (BiosFFsbase+0x10), 1)
				FFSfileChksm = ReadList(BiosBinListBuff, (BiosFFsbase+0x11), 1)
				FFSfileType = ReadList(BiosBinListBuff, (BiosFFsbase+0x12), 1)
				FFSAttr = ReadList(BiosBinListBuff, (BiosFFsbase+0x13), 1)
				FfsHeaderSize = FFS_FILE_HEADER_SIZE
				FFSsize = ReadList(BiosBinListBuff, BiosFFsbase+0x14, 3)
				if(FFSAttr == FFS_ATTRIB_LARGE_FILE):
					FfsHeaderSize = FFS_FILE_HEADER2_SIZE
					FFSsize = ReadList(BiosBinListBuff, BiosFFsbase+FFS_FILE_HEADER_SIZE, 4)
				if ( ((FFsGuid == AllFsGuid) and (FFSsize == 0xFFFFFF)) or (FFSsize == 0) ):
					break	# InValid FFS, break from FFS loop
				FFSsectionSize = ReadList(BiosBinListBuff, BiosFFsbase+FfsHeaderSize, 3)
				FFSsectionType = ReadList(BiosBinListBuff, BiosFFsbase+FfsHeaderSize+3, 1)
				for FileGuid in Files2saveGuidList:
					if ( FFsGuid == FileGuid ):
						FfsFileName = clb.TempFolder+os.sep+"%X_File.ffs" %FFsGuid[0]
						PrintLog(" ++++++++++   Saving FFS file as %s   ++++++++++   |" %FfsFileName, LogFile)
						FfsFile = open(FfsFileName, 'wb')
						FfsFile.write(string.join(BiosBinListBuff[BiosFFsbase:BiosFFsbase+FFSsize], ''))
						FfsFile.close()
						FileGuidListDict[FileSystemSaveCount] = {'FileGuid':FileGuid, 'BiosBinPointer':BiosFFsbase, 'FileSystemSize':FFSsize, 'IsCmprFv': IsCmprFv, 'FvMainCount': FvMainCount}
						FileSystemSaveCount = FileSystemSaveCount + 1
						if(FileSystemSaveCount >= len(Files2saveGuidList)):
							TabLevel = 0
							return
						break
				PrintLog(" BiosFFSbase = 0x%08X  FFSsize : 0x%X  FFShdrChksm 0x%X  FFSfileChksm = 0x%X " %(BiosFFsbase, FFSsize, FFShdrChksm, FFSfileChksm), LogFile)
				PrintLog(" FFSfileType = \"%s\"  FFSAttr = 0x%X " %(FFSfileTypesDict.get(FFSfileType, "NA"), FFSAttr), LogFile)
				PrintLog(" FFSsectionSize = 0x%X  FFSsectionType = \"%s\" " %(FFSsectionSize, FFSsectionTypeDict.get(FFSsectionType, "NA")), LogFile)
				PrintLog(" FFSguid : %s " %GuidStr(FFsGuid), LogFile)
				FoundAlgorithmSha256 = False
				if( (FFSsectionType == EFI_SECTION_GUID_DEFINED) and (SkipGuidedSec == False) ):
					SectionGuid  = FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4))
					FFSsectionDataStart = 0
					if (SectionGuid == gEfiFirmwareContentsSignedGuid):
						SignSecBuffStartOfst = ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4+0x10), 2)
						SignSecBuffSize = ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst), 4)
						if( (gEfiCertTypeRsa2048Sha256Guid == FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst+8))) and (gEfiHashAlgorithmSha256Guid == FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+SignSecBuffStartOfst+0x18))) ):
							FoundAlgorithmSha256 = True
						FFSsectionDataStart = SignSecBuffStartOfst + SignSecBuffSize
						FFSsectionSize = ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart), 3)
						SectionGuid  = FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4))
					if (SectionGuid == gEfiCertTypeRsa2048Sha256Guid):
						# typedef struct {
						# EFI_GUID  HashType;
						# UINT8     PublicKey[256];
						# UINT8     Signature[256];
						# } EFI_CERT_BLOCK_RSA_2048_SHA256;
						SignSecBuffStartOfst = ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+4+0x10), 2)
						if(gEfiHashAlgorithmSha256Guid == FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+0x18))):
							FoundAlgorithmSha256 = True
						FFSsectionDataStart = SignSecBuffStartOfst + 0x210
						FFSsectionSize = ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart), 3)
						SectionGuid  = FetchGuid(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4))
					if ((SectionGuid == gLzmaCustomDecompressGuid) or (SectionGuid == gBrotliCustomDecompressGuid)):
						TabLevel = TabLevel + 1
						if (FFSfileType == FV_FILETYPE_FIRMWARE_VOLUME_IMAGE):
							PrintLog(" Current compressed Section is FIRMWARE_VOLUME_IMAGE, decompresing and parsing it...", LogFile)
						LzmaBuffStart = FFSsectionDataStart+ReadList(BiosBinListBuff, (BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+4+0x10), 2)
						LzmaFvMainCompactBuff = string.join(BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+LzmaBuffStart):(BiosFFsbase+FfsHeaderSize+FFSsectionDataStart+FFSsectionSize)], '')
						TmpFile = open(clb.TempFolder+os.sep+"FvComp.sec", 'wb')
						TmpFile.write(LzmaFvMainCompactBuff)
						TmpFile.close()
						if (SectionGuid == gLzmaCustomDecompressGuid):
							PrintLog(" Found LZMA Compressed section", LogFile)
							if os.name == "nt":
								os.system('%s%sLzmaCompress.exe -q -d %s%sFvComp.sec -o %s%sFwVol.fv' %(clb.XmlCliToolsDir,os.sep, clb.TempFolder, os.sep, clb.TempFolder, os.sep))
							else:
								os.system('%s%sLzmaCompress -q -d %s%sFvComp.sec -o %s%sFwVol.fv' %(clb.XmlCliToolsDir,os.sep, clb.TempFolder, os.sep, clb.TempFolder, os.sep))
						if (SectionGuid == gBrotliCustomDecompressGuid):
							PrintLog(" Found Brotli Compressed section", LogFile)
							if os.name == "nt":
								os.system('%s%sBrotli.exe -d -i %s%sFvComp.sec -o %s%sFwVol.fv' %(clb.XmlCliToolsDir,os.sep, clb.TempFolder, os.sep, clb.TempFolder, os.sep))
							else:
								os.system('%s%sBrotli -d -i %s%sFvComp.sec -o %s%sFwVol.fv' %(clb.XmlCliToolsDir,os.sep, clb.TempFolder, os.sep, clb.TempFolder, os.sep))
						TmpFile = open(clb.TempFolder+os.sep+"FwVol.fv", 'rb')
						FvMainListBuffer = list(TmpFile.read())
						TmpFile.close()
						UcomprsSecSizeOffset = (ReadList(FvMainListBuffer, 0, 2) & 0xFFF)
						TempSizeVar = ReadList(FvMainListBuffer, UcomprsSecSizeOffset, 3)
						if(TempSizeVar != 0xFFFFFF):
							UcomprsSecEndAddr = TempSizeVar + UcomprsSecSizeOffset
							UcomprsSecSizeOffset = UcomprsSecSizeOffset + 4
						else:
							UcomprsSecEndAddr = ReadList(FvMainListBuffer, (UcomprsSecSizeOffset+4), 4) + 8
							UcomprsSecSizeOffset = UcomprsSecSizeOffset + 8
						TempBuff = BiosBinListBuff
						TempBiosFVbase = BiosFvBase
						TempBiosFFsbase = BiosFFsbase
						TempFFSsize = FFSsize
						TempFvSize = FvSize
						if(SaveFvMainFile):
							FvMainCount = FvMainCount + 1
							FvMainCompDict[FvMainCount] = {'FvBaseAddr': BiosFvBase, 'BiosFFsbase': BiosFFsbase, 'FfsHeaderSize':FfsHeaderSize, 'LzmaBuffStart':LzmaBuffStart, 'UcomprsSecSizeOffset': UcomprsSecSizeOffset, 'FoundAlgorithmSha256': FoundAlgorithmSha256}
							PrintLog(" ++++++++++   Saving the decompressed FV file as %s   ++++++++++   |" %FvMainFileName.replace('FvMain_0.fv', 'FvMain_%d.fv' %FvMainCount), LogFile)
							clb.RenameFile(clb.TempFolder+os.sep+"FwVol.fv", FvMainFileName.replace('FvMain_0.fv', 'FvMain_%d.fv' %FvMainCount))		# Save for future use
							clb.RenameFile(clb.TempFolder+os.sep+"FvComp.sec", clb.TempFolder+os.sep+"FvMainCompOrg_%d.sec" %FvMainCount)		# Save for future use
						clb.RemoveFile(clb.TempFolder+os.sep+"FwVol.fv")
						clb.RemoveFile(clb.TempFolder+os.sep+"FvComp.sec")
						ProcessBin(FvMainListBuffer[UcomprsSecSizeOffset:UcomprsSecEndAddr], 0, Files2saveGuidList, LogFile, False, True)
						IsCmprFv=False
						PrintLog(" Uncompressed FIRMWARE_VOLUME_IMAGE parsing complete...", LogFile)
						BiosBinListBuff = TempBuff
						BiosFvBase = TempBiosFVbase
						BiosFFsbase = TempBiosFFsbase
						FFSsize = TempFFSsize
						FvSize = TempFvSize
						TabLevel = TabLevel - 1
						if( (FileSystemSaveCount != 0) and (FileSystemSaveCount >= len(Files2saveGuidList)) ):
							TabLevel = 0
							return
				BiosFFsbase = (BiosFFsbase + FFSsize + 7 ) & 0xFFFFFFF8		# this is because FFS sits on a 8 byte boundary
				PrintLog("-------------------------------------------------------------------------------------", LogFile)
			TabLevel = TabLevel - 1
			PrintLog("-----------------------------------------------------------------------------------------------------", LogFile)
			BiosFvBase = (BiosFvBase + FvSize)
		else:
			BiosFvBase = ((BiosFvBase & 0xFFFFF000) + 0x1000)		# InValid FV, Adjust FvBaseAccrodingly

def UpdateFvMainComp(BiosBinListBuff):
	global FvMainCompDict

	if(len(FvMainCompDict) == 0):
		print "null FvMainCompDict, hence returning from UpdateFvMainComp()"
		return

	EncryptionAlgoValid = False
	Sha256AlgoValid = False
	NewFvFileList = glob.glob(os.sep.join([clb.TempFolder, "FvMain_*_New.fv"]))
	for NewFvFile in NewFvFileList:
		match = re.search(r"FvMain_(\d*)_New.fv", NewFvFile)
		if(match == None):
			coninue
		FvCount = eval(match.group(1))
		Sha256Algo = FvMainCompDict[FvCount]['FoundAlgorithmSha256']
		TmpFile = open(clb.TempFolder+os.sep+"FvMainCompOrg_%d.sec" %FvCount, 'rb')
		OrgFvCompBuff = TmpFile.read()
		TmpFile.close()
		OrgFvCompSize = len(OrgFvCompBuff)
		if (EncryptionAlgoValid == False):
			OrgFvFile = os.sep.join([clb.TempFolder, "FvMain_%d.fv" %FvCount])
			print "\nUpdateHiiDb Defaults Enabled, Testing our Encryption algorithm & verifying, this may take few seconds.."
			if os.name == "nt":
				os.system('%s%sLzmaCompress.exe -q -e %s -o %s%sFvMainComp_%d.sec' %(clb.XmlCliToolsDir, os.sep, OrgFvFile, clb.TempFolder, os.sep, FvCount))
			else:
				os.system('%s%sLzmaCompress -q -e %s -o %s%sFvMainComp_%d.sec' %(clb.XmlCliToolsDir, os.sep, OrgFvFile, clb.TempFolder, os.sep, FvCount))
			if (filecmp.cmp(clb.TempFolder+os.sep+"FvMainComp_%d.sec" %FvCount, clb.TempFolder+os.sep+"FvMainCompOrg_%d.sec" %FvCount)):
				print "Hurray!! Our Encryption algorithm matches with given Bios Binary!, we can now proceed\n"
				EncryptionAlgoValid = True
			if( (Sha256Algo) and (Sha256AlgoValid == False) ):
				# print "Found that FV Main was signed using Sha256Algo"
				BiosFFsbase = FvMainCompDict[FvCount]['BiosFFsbase']
				FfsHeaderSize = FvMainCompDict[FvCount]['FfsHeaderSize']
				LzmaBuffStart = FvMainCompDict[FvCount]['LzmaBuffStart']
				OrgFvCompBuffList = BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+0x30):(BiosFFsbase+FfsHeaderSize+LzmaBuffStart+OrgFvCompSize)]
				TmpFile = open('%s%sFvMainComp_%d_temp.guided' %(clb.TempFolder, os.sep, FvCount), 'wb')
				TmpFile.write(string.join(BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+0x30+0x210):(BiosFFsbase+FfsHeaderSize+0x30+0x210+0x18)], ''))
				TmpFile.write(OrgFvCompBuff)
				TmpFile.close()
				if os.name == "nt":
					os.system('%s%sLzmaCompress.exe -q -d %s%sVaiyaktikChavi.bin -o %s%sTempJlt.bin' %(clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep))
					os.system('%s%sRsa2048Sha256Sign.exe -q -e --private-key %s%sTempJlt.bin -o %s%sFvMainCompShaFull_%d_New.tmp %s%sFvMainComp_%d_temp.guided' %(clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep, clb.TempFolder, os.sep,  FvCount, clb.TempFolder, os.sep, FvCount))
				else:
					os.system('%s%sLzmaCompress -q -d %s%sVaiyaktikChavi.bin -o %s%sTempJlt.bin' %(clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep))
					assert False, "RSA Application is not supported for Linux"
				TmpFile = open(clb.TempFolder+os.sep+"FvMainCompShaFull_%d_New.tmp" %FvCount, 'rb')
				TempFvCompBuffList = list(TmpFile.read())
				TmpFile.close()
				if(TempFvCompBuffList == OrgFvCompBuffList):
					# print "Sha256 signaturing algorithm matches as well, we can now truly proceed!!"
					Sha256AlgoValid = True

		if(EncryptionAlgoValid):
			print "\nNow Encrypting FvMain_%d_New.fv and generating new Bios image, this may take few seconds.." %FvCount
			if os.name == "nt":
				os.system('%s%sLzmaCompress.exe -q -e %s%sFvMain_%d_New.fv -o %s%sFvMainComp_%d_New.sec' %(clb.XmlCliToolsDir, os.sep, clb.TempFolder, os.sep, FvCount, clb.TempFolder, os.sep, FvCount))
			else:
				os.system('%s%sLzmaCompress -q -e %s%sFvMain_%d_New.fv -o %s%sFvMainComp_%d_New.sec' %(clb.XmlCliToolsDir, os.sep, clb.TempFolder, os.sep, FvCount, clb.TempFolder, os.sep, FvCount))
			TmpFile = open(clb.TempFolder+os.sep+"FvMainComp_%d_New.sec" %FvCount, 'rb')
			NewFvCompBuff = TmpFile.read()
			TmpFile.close()
			NewFvCompBuffList = list(NewFvCompBuff)
			NewFvCompSize = len(NewFvCompBuffList)
			if( (Sha256Algo) and (Sha256AlgoValid) ):
				clb.RemoveFile('%s%sFvMainComp_%d_temp.guided' %(clb.TempFolder, os.sep, FvCount))
				clb.RemoveFile('%s%sFvMainCompShaFull_%d_New.tmp' %(clb.TempFolder, os.sep, FvCount))
				TmpFile = open('%s%sFvMainComp_%d_temp.guided' %(clb.TempFolder, os.sep, FvCount), 'wb')
				NewSecSizeList = []
				NewSecSizeList.insert(0, str(chr((NewFvCompSize+FfsHeaderSize) & 0xFF)))
				NewSecSizeList.insert(1, str(chr(((NewFvCompSize+FfsHeaderSize) >> 8) & 0xFF)))
				NewSecSizeList.insert(2, str(chr(((NewFvCompSize+FfsHeaderSize) >> 16) & 0xFF)))
				TmpFile.write(string.join(NewSecSizeList, ''))
				TmpFile.write(string.join(BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+0x33+0x210):(BiosFFsbase+FfsHeaderSize+0x33+0x210+0x15)], ''))
				TmpFile.write(NewFvCompBuff)
				TmpFile.close()
				if os.name == "nt":
					os.system('%s%sRsa2048Sha256Sign.exe -q -e --private-key %s%sTempJlt.bin -o %s%sFvMainCompShaFull_%d_New.tmp %s%sFvMainComp_%d_temp.guided' %(clb.XmlCliToolsDir, os.sep, clb.XmlCliToolsDir, os.sep, clb.TempFolder, os.sep, FvCount, clb.TempFolder, os.sep, FvCount))
				else:
					assert False, "RSA Utility is not supported in linux yet."
				TmpFile = open(clb.TempFolder+os.sep+"FvMainCompShaFull_%d_New.tmp" %FvCount, 'rb')
				NewFvCompShaFullBuffList = list(TmpFile.read())
				TmpFile.close()
			if(NewFvCompSize != 0):
				BiosFFsbase = FvMainCompDict[FvCount]['BiosFFsbase']
				FfsHeaderSize = FvMainCompDict[FvCount]['FfsHeaderSize']
				LzmaBuffStart = FvMainCompDict[FvCount]['LzmaBuffStart']
				if( (Sha256Algo) and (Sha256AlgoValid) ):
					BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+0x30):(BiosFFsbase+FfsHeaderSize+LzmaBuffStart+NewFvCompSize)] = NewFvCompShaFullBuffList
				else:
					BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+LzmaBuffStart):(BiosFFsbase+FfsHeaderSize+LzmaBuffStart+NewFvCompSize)] = NewFvCompBuffList
				if(NewFvCompSize < OrgFvCompSize):
					for ByteCount in range (0, (OrgFvCompSize-NewFvCompSize)):
						BiosBinListBuff[(BiosFFsbase+FfsHeaderSize+LzmaBuffStart+NewFvCompSize+ByteCount)] = '\xff'
				NewFvCompSize = NewFvCompSize + LzmaBuffStart
				BiosBinListBuff.pop(BiosFFsbase+0x14)
				BiosBinListBuff.pop(BiosFFsbase+0x14)
				BiosBinListBuff.pop(BiosFFsbase+0x14)
				BiosBinListBuff.insert((BiosFFsbase+0x14), str(chr((NewFvCompSize+FfsHeaderSize) & 0xFF)))
				BiosBinListBuff.insert((BiosFFsbase+0x15), str(chr(((NewFvCompSize+FfsHeaderSize) >> 8) & 0xFF)))
				BiosBinListBuff.insert((BiosFFsbase+0x16), str(chr(((NewFvCompSize+FfsHeaderSize) >> 16) & 0xFF)))
				BiosBinListBuff.pop(BiosFFsbase+FfsHeaderSize)
				BiosBinListBuff.pop(BiosFFsbase+FfsHeaderSize)
				BiosBinListBuff.pop(BiosFFsbase+FfsHeaderSize)
				BiosBinListBuff.insert((BiosFFsbase+FfsHeaderSize), str(chr(NewFvCompSize & 0xFF)))
				BiosBinListBuff.insert((BiosFFsbase+FfsHeaderSize+1), str(chr((NewFvCompSize >> 8) & 0xFF)))
				BiosBinListBuff.insert((BiosFFsbase+FfsHeaderSize+2), str(chr((NewFvCompSize >> 16) & 0xFF)))
				NewFFsHdrCheckSum = 0
				for  Count in range (0, 0x17):
					if (Count != 0x11) and (Count != 0x10):
						NewFFsHdrCheckSum = (NewFFsHdrCheckSum + int(clb.ReadList(BiosBinListBuff, BiosFFsbase+Count, 1))) & 0xFF
				NewFFsHdrCheckSum = (0x100 - NewFFsHdrCheckSum) & 0xFF
				BiosBinListBuff.pop(BiosFFsbase+0x10)
				BiosBinListBuff.insert(BiosFFsbase+0x10, str(chr(NewFFsHdrCheckSum)))
		else:
			print "Files are different, Our Encryption algorithm doesnt match with the given BIOS binary\n"
	clb.RemoveFile(clb.XmlCliToolsDir+os.sep+'TempJlt.bin')

def UpdateBiosId(BiosBinaryFile=0, NewMajorVer="", NewMinorVer="", OutFolder=0, NewBiosVer="", NewTsVer=""):
	global FileGuidListDict, FwpPrintEn, SaveFvMainFile
	tmpPrintSts = FwpPrintEn
	FwpPrintEn = False
	FileGuidListDict = {}
	FvMainCount = 0
	BiosIdFfsToSave  = [ gEfiBiosIdGuid ]
	BiosIdString = "Unknown"
	NewBiosId = BiosIdString
	clb.OutBinFile = ""

	if(OutFolder == 0):
		OutFolder = clb.TempFolder
	DelTempFvFfsFiles(clb.TempFolder)
	BiosBinFile = open(BiosBinaryFile, "rb")
	BiosBinListBuff = list(BiosBinFile.read())
	BiosBinFile.close()
	BiosFileName = os.path.basename(BiosBinaryFile)
	FlashRegionInfo(BiosBinListBuff, False)
	if (FwIngrediantDict['FlashDescpValid'] != 0):
		BiosRegionBase = FwIngrediantDict['FlashRegions'][BIOS_Region]['BaseAddr']
		BiosEnd = FwIngrediantDict['FlashRegions'][BIOS_Region]['EndAddr'] + 1
	else:
		BiosRegionBase = 0
		BiosEnd = len(BiosBinListBuff)

	if(len(BiosBinListBuff) != 0):
		SaveFvMainFile = False
		ProcessBin(BiosBinListBuff, BiosRegionBase, BiosIdFfsToSave, 0, True, BiosRegionEnd=BiosEnd)
		for FileGuid in BiosIdFfsToSave:		# Delete the file once done, dont want the stale file affecting subsequent operation
			clb.RemoveFile(clb.TempFolder+os.sep+"%X_File.ffs" %FileGuid[0])
			clb.RemoveFile(clb.TempFolder+os.sep+"%X_File.fv" %FileGuid[0])
		for FileCountId in FileGuidListDict:
			if(FileGuidListDict[FileCountId]['FileGuid'] == gEfiBiosIdGuid):
				BiosIdSecBase = FileGuidListDict[FileCountId]['BiosBinPointer'] + FFS_FILE_HEADER_SIZE + EFI_COMMON_SECTION_HEADER_SIZE
				FfsSize = FileGuidListDict[FileCountId]['FileSystemSize']
				BiosIdString = ""
				BiosIdSig = ReadList(BiosBinListBuff, BiosIdSecBase, 8)
				if(BiosIdSig != 0):
					for count in range (0, (FfsSize-FFS_FILE_HEADER_SIZE-EFI_COMMON_SECTION_HEADER_SIZE)):
						ChrVal = ReadList(BiosBinListBuff, (BiosIdSecBase+8+(count*2)), 1)
						if(ChrVal == 0):
							break
						BiosIdString = BiosIdString + chr(ChrVal)
				print "Current BIOS ID String is %s" %(BiosIdString)
				if(BiosIdString != "Unknown"):
					if (NewBiosVer == "") and (NewMajorVer == "") and (NewMinorVer == "") and (NewTsVer == ""):
						print "Ver, Major, Minor, and TS are empty, so no action taken."
					else:
						NewBiosId = BiosIdString.split('.')
						if(NewMajorVer != ""):
							NewBiosId[2] = NewMajorVer.zfill(4)[0:4]
						if(NewMinorVer != ""):
							NewBiosId[3] = NewMinorVer.zfill(3)[0:3]
						if(NewBiosVer != ""):
							NewBiosId[1] = NewBiosVer.zfill(3)[0:3]
						else:
							NewBiosId[1] = "E9I"	# indicates that the BIOS ID was updated using external Tool.
						if(NewTsVer != ""):
							NewBiosId[4] = NewTsVer.zfill(10)[0:10]
						else:
							CurTime = time.localtime()
							NewBiosId[4] = '%02d%02d%02d%02d%02d' %((CurTime[0]-2000), CurTime[1], CurTime[2], CurTime[3], CurTime[4])
						NewBiosIdString = string.join(NewBiosId, '.')
						print "Updated BIOS ID String is %s" %(NewBiosIdString)
						for count in range (0, len(NewBiosIdString)):
							ChrVal = ReadList(BiosBinListBuff, (BiosIdSecBase+8+(count*2)), 1)
							if(ChrVal == 0):
								break
							BiosBinListBuff.pop((BiosIdSecBase+8+(count*2)))
							BiosBinListBuff.insert((BiosIdSecBase+8+(count*2)), NewBiosIdString[count])
						NewBiosFileName = BiosFileName.replace(BiosIdString, NewBiosIdString)
						if(NewBiosFileName == BiosFileName):
							NewBiosFileName = NewBiosIdString+'.bin'
						NewBiosBinFile = OutFolder+os.sep+NewBiosFileName
						clb.OutBinFile = NewBiosBinFile
						ModBiosBinFile = open(NewBiosBinFile, "wb")
						ModBiosBinFile.write(string.join(BiosBinListBuff, ''))
						ModBiosBinFile.close()
						print "Bios Binary with updated BIOS ID is saved under %s" %NewBiosBinFile
					break
	FwpPrintEn = tmpPrintSts

OldBinNvarNameDict = { 0: "Setup", 1: "ServerMgmt"}
OldBinNvarNameDictPly = { 0 :"Setup", 1 :"SocketIioConfig", 2 :"SocketCommonRcConfig", 3 :"SocketMpLinkConfig", 4 :"SocketMemoryConfig", 5 :"SocketMiscConfig", 6 :"SocketPowerManagementConfig", 7 :"SocketProcessorCoreConfig", 8 :"SvOtherConfiguration", 9 :"SvPchConfiguration" }

def BiosKnobsDataBinParser(BiosKnobBinFile, BiosIdString=""):
	BiosKnobFile = open(BiosKnobBinFile, "rb")
	BiosKnobBinBuff = list(BiosKnobFile.read())
	BiosKnobFile.close()
	BiosKnobDict = {}
	BiosKnobBinEndAddr = ReadList(BiosKnobBinBuff, 0x18, 3)
	BiosKnobBinPtr = 0x1C
	OldBinFileFormat = False
	KnobBinRevision = 0
	DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD
	while(BiosKnobBinPtr < BiosKnobBinEndAddr):
		BinHdrSig = binascii.unhexlify(hex(ReadList(BiosKnobBinBuff, BiosKnobBinPtr, 5)).strip('L')[2:])[::-1]
		VarId = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+5, 1)
		KnobCount = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+6, 2)
		if( (BinHdrSig == "$NVAR") and (KnobCount != 0) ):
			#PrintLog("----    Current Ptr = 0x%X    VarId = %d    ---" %(BiosKnobBinPtr, VarId), LogFile)
			DupKnobBufOff = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+8, 3)
			NvarPktSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+0xB, 3)
			NvarSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+0xE, 2)
			NvarGuid = ZeroGuid
			if (NvarSize == 0):
				OldBinFileFormat = True
				DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_OLD
				if (BiosIdString[0:3] == "PLY"):
					NvarName = OldBinNvarNameDictPly[VarId]	# this is an assumption if we still have old Bin format, so that we are backward compatible
				else:
					NvarName = OldBinNvarNameDict[VarId]	# this is an assumption if we still have old Bin format, so that we are backward compatible
				tmpBiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
			else:	# New Format
				OldBinFileFormat = False
				KnobBinRevision = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr+BIOS_KNOB_BIN_REVISION_OFFSET), 1)
				if(KnobBinRevision >= 2): # revision equal or higher than 0.2?
					NvarGuid = FetchGuid(BiosKnobBinBuff, (BiosKnobBinPtr+BIOS_KNOB_BIN_GUID_OFFSET))
				NvarNameOfst = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr+NVAR_NAME_OFFSET), 1)
				NvarName = ""
				for VarSizeCount in range (0, 0x30):
					Val = ReadList(BiosKnobBinBuff, (BiosKnobBinPtr+NvarNameOfst+VarSizeCount), 1)
					if(Val == 0):
						break
					NvarName = NvarName + chr(Val)
				if(KnobBinRevision >= 3): # revision equal or higher than 0.3?
					DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE_V03
				else:
					DataBinHdrSize = BIOS_KNOBS_DATA_BIN_HDR_SIZE
				tmpBiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
			BiosKnobDict[VarId]={'HiiVarId':0xFF, 'HiiVarSize':0, 'KnobDict':{}, 'DupKnobDict':{}, 'NvarName':NvarName, 'NvarGuid':NvarGuid, 'NvarSize':NvarSize, 'KnobCount':KnobCount}
			TmpKnobDict = {}
			while( tmpBiosKnobBinPtr < (BiosKnobBinPtr+DupKnobBufOff) ):
				KnobOffset = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, 2)
				if(OldBinFileFormat):
					tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + 2
					KnobSize_bin = INVALID_KNOB_SIZE
					SetupTypeBin = INVALID_KNOB_SIZE
				else:
					KnobInfo = ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr+2, 1)
					tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + 3
					KnobType_bin = ((KnobInfo >> 4) & 0xF)
					if(KnobType_bin >= 0x8):
						KnobType_bin = 0x8
						KnobSize_bin = (KnobInfo & 0x7F) * 2
					else:
						KnobSize_bin = (KnobInfo & 0x0F)
						if( (KnobBinRevision >= 3) and (KnobType_bin < 0x4) ):
							KnobType_bin = KnobType_bin + 0x4		# This indicates that current Knob entry is part of Depex, Adjust the Type accordingly.
					SetupTypeBin = SetupTypeBin2ValDict.get(KnobType_bin, INVALID_KNOB_SIZE)
				StrSize = 0
				while(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr+StrSize, 1)):
					StrSize = StrSize + 1
				if(StrSize):
					KnobName = binascii.unhexlify(hex(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize)).strip('L')[2:])[::-1]
				else:
					KnobName = ""
				tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
				StrSize = 0
				while(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr+StrSize, 1)):
					StrSize = StrSize + 1
				if(StrSize):
					KnobDepex = binascii.unhexlify(hex(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize)).strip('L')[2:])[::-1]
				else:
					KnobDepex = "TRUE"
				tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
				TmpKnobDict[KnobOffset] = { 'SetupTypeHii':0, 'SetupTypeBin':SetupTypeBin, 'KnobName':KnobName, 'KnobSzHii':0, 'KnobSzBin':KnobSize_bin, 'HiiDefVal':0, 'Depex':KnobDepex, 'Prompt':0, 'Help':0, 'ParentPromptList': [], 'Min':0, 'Max':0, 'Step':0, 'KnobPrsd':[0, 0, 0xFF], 'OneOfOptionsDict':{} }
			BiosKnobDict[VarId]['KnobDict'] = TmpKnobDict

			tmpBiosKnobBinPtr = (BiosKnobBinPtr+DupKnobBufOff)		# Parse Duplicate list
			TmpDupKnobDict = {}
			DupCount = 0
			while( tmpBiosKnobBinPtr < (BiosKnobBinPtr+NvarPktSize) ):
				StrSize = 0
				while(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr+StrSize, 1)):
					StrSize = StrSize + 1
				if(StrSize):
					DupKnobName = binascii.unhexlify(hex(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize)).strip('L')[2:])[::-1]
				else:
					DupKnobName = ""
				tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
				StrSize = 0
				while(ReadList(BiosKnobBinBuff, (tmpBiosKnobBinPtr+StrSize), 1)):
					StrSize = StrSize + 1
				if(StrSize):
					DupKnobDepex = binascii.unhexlify(hex(ReadList(BiosKnobBinBuff, tmpBiosKnobBinPtr, StrSize)).strip('L')[2:])[::-1]
				else:
					DupKnobDepex = "TRUE"
				tmpBiosKnobBinPtr = tmpBiosKnobBinPtr + StrSize + 1
				TmpDupKnobDict[DupCount] = { 'DupKnobName':DupKnobName, 'DupDepex':DupKnobDepex }
				DupCount = DupCount + 1
			BiosKnobDict[VarId]['DupKnobDict'] = TmpDupKnobDict
			BiosKnobBinPtr = BiosKnobBinPtr + NvarPktSize
		elif(BinHdrSig == "$NVRO"):
			NvarPktSize = ReadList(BiosKnobBinBuff, BiosKnobBinPtr+0xB, 3)
			BiosKnobBinPtr = BiosKnobBinPtr + NvarPktSize
		else:
			BiosKnobBinPtr = BiosKnobBinPtr + DataBinHdrSize
	return BiosKnobDict

#
#   typedef UINT16  EFI_QUESTION_ID;
#   typedef UINT16  EFI_STRING_ID;
#   typedef UINT16  EFI_FORM_ID;
#   typedef UINT16  EFI_VARSTORE_ID;
#
#   typedef struct _EFI_IFR_OP_HEADER {
#     UINT8                    OpCode;
#     UINT8                    Length:7;
#     UINT8                    Scope:1;
#   } EFI_IFR_OP_HEADER;
#
#    typedef struct _EFI_IFR_STATEMENT_HEADER {
#      EFI_STRING_ID            Prompt;
#      EFI_STRING_ID            Help;
#    } EFI_IFR_STATEMENT_HEADER;
#    
#    typedef struct _EFI_IFR_QUESTION_HEADER {
#      EFI_IFR_STATEMENT_HEADER Header;
#      EFI_QUESTION_ID          QuestionId;
#      EFI_VARSTORE_ID          VarStoreId;
#      union {
#        EFI_STRING_ID          VarName;
#        UINT16                 VarOffset;
#      }                        VarStoreInfo;
#      UINT8                    Flags;
#    } EFI_IFR_QUESTION_HEADER;
#
#    typedef struct _EFI_IFR_VARSTORE {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_GUID                 Guid;
#      EFI_VARSTORE_ID          VarStoreId;
#      UINT16                   Size;
#      UINT8                    Name[1];
#    } EFI_IFR_VARSTORE;
#
#    typedef struct _EFI_IFR_VARSTORE_EFI {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_VARSTORE_ID          VarStoreId;
#      EFI_GUID                 Guid;
#      UINT32                   Attributes;
#      UINT16                   Size;
#      UINT8                    Name[1];
#    } EFI_IFR_VARSTORE_EFI;
#
#    typedef struct _EFI_IFR_ONE_OF {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_IFR_QUESTION_HEADER  Question;
#      UINT8                    Flags;
#      MINMAXSTEP_DATA          data;
#    } EFI_IFR_ONE_OF;
#
#    typedef struct _EFI_IFR_STRING {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_IFR_QUESTION_HEADER  Question;
#      UINT8                    MinSize;
#      UINT8                    MaxSize;
#      UINT8                    Flags;
#    } EFI_IFR_STRING;
#
#    typedef struct _EFI_IFR_NUMERIC {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_IFR_QUESTION_HEADER  Question;
#      UINT8                    Flags;
#      MINMAXSTEP_DATA          data;
#    } EFI_IFR_NUMERIC;
#
#    typedef struct _EFI_IFR_CHECKBOX {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_IFR_QUESTION_HEADER  Question;
#      UINT8                    Flags;
#    } EFI_IFR_CHECKBOX;
#
#    typedef struct _EFI_IFR_ONE_OF_OPTION {
#      EFI_IFR_OP_HEADER        Header;
#      EFI_STRING_ID            Option;
#      UINT8                    Flags;
#      UINT8                    Type;
#      EFI_IFR_TYPE_VALUE       Value;
#    } EFI_IFR_ONE_OF_OPTION;
#
#    typedef struct _EFI_IFR_DEFAULT {
#      EFI_IFR_OP_HEADER        Header;
#      UINT16                   DefaultId;
#      UINT8                    Type;
#      EFI_IFR_TYPE_VALUE       Value;
#    } EFI_IFR_DEFAULT;
#
#    typedef struct {
#      UINT16  Year;
#      UINT8   Month;
#      UINT8   Day;
#      UINT8   Hour;
#      UINT8   Minute;
#      UINT8   Second;
#      UINT8   Pad1;
#      UINT32  Nanosecond;
#      INT16   TimeZone;
#      UINT8   Daylight;
#      UINT8   Pad2;
#    } EFI_TIME;
#
#    typedef struct {
#      EFI_GUID  Signature;
#      UINT32  Size;
#      UINT8   Format;
#      UINT8   State;
#      UINT16  Reserved;
#      UINT32  Reserved1;
#    } VARIABLE_STORE_HEADER;
#
#    typedef struct {
#      UINT16      StartId;
#      UINT8       State;
#      UINT8       Reserved;
#      UINT32      Attributes;
#      UINT64      MonotonicCount;
#      EFI_TIME    TimeStamp;
#      UINT32      PubKeyIndex;
#      UINT32      NameSize;
#      UINT32      DataSize;
#      EFI_GUID    VendorGuid;
#    } VARIABLE_HEADER2;
#
#    typedef struct {
#      UINT16      StartId;
#      UINT8       State;
#      UINT8       Reserved;
#      UINT32      Attributes;
#      UINT32      NameSize;
#      UINT32      DataSize;
#      EFI_GUID    VendorGuid;
#    } VARIABLE_HEADER;
#
VARIABLE_HEADER_ALIGNMENT         = 4
VARIABLE_DATA                     = 0x55AA
VARIABLE_STORE_FORMATTED          = 0x5a
VARIABLE_STORE_HEALTHY            = 0xfe
VAR_IN_DELETED_TRANSITION         = 0xfe  # Variable is in obsolete transition.
VAR_DELETED                       = 0xfd  # Variable is obsolete.
VAR_HEADER_VALID_ONLY             = 0x7f  # Variable header has been valid.
VAR_ADDED                         = 0x3f  # Variable has been completely added.
VARIABLE_STORE_HEADER_SIZE        = 0x1C
VARIABLE_HEADER2_SIZE             = 0x3C
VARIABLE_HEADER_SIZE              = 0x20

def ParseNvram(NvRamFvListBuffer, BiosKnobDict, NvRamPointer=0, LogFile=0):
	BiosKnobDictLen = len(BiosKnobDict)
	PrintLog(" Parse Full NvRam VarStores and Knob details ", LogFile)
	NvRamDict = {}
	VarCount = 0
	if(NvRamPointer == 0):
		for CurrPtr in range (NvRamPointer, (len(NvRamFvListBuffer)-0x10)):
			VarStoreHdrGuid = FetchGuid(NvRamFvListBuffer, CurrPtr)
			if( (VarStoreHdrGuid == gEfiGlobalVariableGuid) or (VarStoreHdrGuid == gEfiAuthenticatedVariableGuid) or (VarStoreHdrGuid == gEfiVariableGuid) ):
				NvRamPointer = CurrPtr
				PrintLog(" Found NvRam Start at 0x%X offset" %NvRamPointer, LogFile)
				break
	for VarStrHdrCount in range (0, 0x100):
		if(NvRamPointer >= (len(NvRamFvListBuffer)-VARIABLE_STORE_HEADER_SIZE)):
			return NvRamDict
		VarStoreHdrGuid = FetchGuid(NvRamFvListBuffer, NvRamPointer)
		VarStoreSize = ReadList(NvRamFvListBuffer, (NvRamPointer+0x10), 4)
		if( (VarStoreHdrGuid == AllFsGuid) or (VarStoreSize == 0xFFFFFFFF) ):
			break
		if( (VarStoreHdrGuid == gEfiGlobalVariableGuid) or (VarStoreHdrGuid == gEfiAuthenticatedVariableGuid) ):
			HdrSize = VARIABLE_HEADER2_SIZE
			NameSzOffst = 0x24
			DataSzOffst = 0x28
			GuidOffset = 0x2C
		elif(VarStoreHdrGuid == gEfiVariableGuid):
			HdrSize = VARIABLE_HEADER_SIZE
			NameSzOffst = 0x08
			DataSzOffst = 0x0C
			GuidOffset = 0x10
		else:
			HdrSize = VARIABLE_HEADER_SIZE
			NameSzOffst = 0x08
			DataSzOffst = 0x0C
			GuidOffset = 0x10
		VarStoreFormat = ReadList(NvRamFvListBuffer, (NvRamPointer+0x14), 1)
		VarStoreState = ReadList(NvRamFvListBuffer, (NvRamPointer+0x15), 1)
		PrintLog(" CurrPtr = 0x%X  VarStoreSize = 0x%X" %(NvRamPointer, VarStoreSize), LogFile)
		PrintLog(" VarStoreHdr Guid = %s " %GuidStr(VarStoreHdrGuid), LogFile)
		if( (VarStoreFormat != VARIABLE_STORE_FORMATTED) or (VarStoreState != VARIABLE_STORE_HEALTHY) ):
			NvRamPointer = NvRamPointer + VarStoreSize
			break
		CurVarPtr = ((NvRamPointer + VARIABLE_STORE_HEADER_SIZE + 3) & 0xFFFFFFFC)	# this one is 4 bytes or dword aligned always
		PrintLog ("------------|--------|------------|------------|--------------------------------|-------------", LogFile)
		PrintLog (" CurrentPtr | State  | Atribute   | NvarDataSz | VarName                        | VarGuid     ", LogFile)
		PrintLog ("------------|--------|------------|------------|--------------------------------|-------------", LogFile)
		for count in range (0, 200):
			StartId = ReadList(NvRamFvListBuffer, CurVarPtr, 2)
			if(StartId != VARIABLE_DATA):
				CurVarPtr = CurVarPtr + HdrSize
				break
			VarState = ReadList(NvRamFvListBuffer, (CurVarPtr+0x2), 1)
			VarAtri = ReadList(NvRamFvListBuffer, (CurVarPtr+0x4), 4)
			VarNameSize = ReadList(NvRamFvListBuffer, (CurVarPtr+NameSzOffst), 4)
			VarDataSize = ReadList(NvRamFvListBuffer, (CurVarPtr+DataSzOffst), 4)
			VarGuid = FetchGuid(NvRamFvListBuffer, (CurVarPtr+GuidOffset))
			VarName = ""
			for index in range (0, (VarNameSize/2)):
				Val = ReadList(NvRamFvListBuffer, (CurVarPtr+HdrSize+(index*2)), 1)
				if(Val == 0):
					break
				VarName = VarName + chr(Val)
			PrintLog (" 0x%-8X |  0x%02X  | 0x%08X | 0x%-8X | %-30s | %s" %(CurVarPtr, VarState, VarAtri, VarDataSize, VarName, GuidStr(VarGuid)), LogFile)
			PrintLog ("------------|--------|------------|------------|--------------------------------|-------------", LogFile)
			if(BiosKnobDictLen):
				for VarId in BiosKnobDict:
					if( (VarName == BiosKnobDict[VarId]['NvarName']) and ((BiosKnobDict[VarId]['NvarGuid'] == ZeroGuid) or (VarGuid == BiosKnobDict[VarId]['NvarGuid'])) ):
						NvRamDict[VarId] = { 'NvarName':VarName, 'NvarGuid':VarGuid, 'NvarSize':VarDataSize, 'VarAttri':VarAtri, 'NvarDataBufPtr':(CurVarPtr+HdrSize+VarNameSize) }
						break
			else:
				NvRamDict[VarCount] = { 'NvarName':VarName, 'NvarGuid':VarGuid, 'NvarSize':VarDataSize, 'VarAttri':VarAtri, 'NvarDataBufPtr':(CurVarPtr+HdrSize+VarNameSize) }
				VarCount = VarCount + 1
			CurVarPtr = (CurVarPtr + HdrSize + VarNameSize + VarDataSize + 3) & 0xFFFFFFFC
		NvRamPointer = NvRamPointer + VarStoreSize
	return NvRamDict

def GetIfrFormsHdr(HiiDbBinListBuff, HiiDbPointer=0):
	if( HiiDbBinListBuff == 0 ):
		return 0
	ReturnAddrDict = { 'IfrList' : [], 'StrPkgHdr' : 0, 'UqiPkgHdr' : 0}
	BufLen = len(HiiDbBinListBuff)
	while(HiiDbPointer < BufLen):
		Guid_LowHalf = ReadList(HiiDbBinListBuff, HiiDbPointer, 4)
		if (Guid_LowHalf == gEfiIfrTianoGuid[0]):
			HiiLstGuid  = FetchGuid(HiiDbBinListBuff, HiiDbPointer)
			if(HiiLstGuid == gEfiIfrTianoGuid):
				IfrOpcode = ReadList(HiiDbBinListBuff, HiiDbPointer - 2, 1)
				if (IfrOpcode == EFI_IFR_GUID_OP):
					TmpHiiDbPtr = HiiDbPointer - 2
					StartAddress = 0
					if(ReadList(HiiDbBinListBuff, HiiDbPointer - 2 - 0x27, 2) == 0xA70E):  # Check if we Find formset opcode
						StartAddress = HiiDbPointer - 2 - 0x27
					StartFound = False
					for count in range (0, 0x1000):
						IfrOpcode = ReadList(HiiDbBinListBuff, TmpHiiDbPtr, 1)
						IfrOpLen = (ReadList(HiiDbBinListBuff, (TmpHiiDbPtr+1), 1) & 0x7F)
						if ( (IfrOpcode == EFI_IFR_VARSTORE_OP) or (IfrOpcode == EFI_IFR_VARSTORE_EFI_OP) ):
							StartFound = True
							break
						TmpHiiDbPtr = TmpHiiDbPtr + IfrOpLen
					if(StartFound):
						if(StartAddress != 0):
							ReturnAddrDict['IfrList'].append(StartAddress)
						HiiDbPointer = TmpHiiDbPtr
		if (Guid_LowHalf == 0x552D6E65):		# compare with "en-US"
			StringPkgLang = ReadList(HiiDbBinListBuff, HiiDbPointer, 6)
			if (StringPkgLang == 0x53552D6E65):		# compare with "en-US"
				StringHdr = ReadList(HiiDbBinListBuff, (HiiDbPointer+0x6), 1)
				PromptLow = ReadList(HiiDbBinListBuff, (HiiDbPointer+0x7), 8)
				PromptHigh = ReadList(HiiDbBinListBuff, (HiiDbPointer+0x7+0x8), 8)
				if( (StringHdr == EFI_HII_SIBT_STRING_UCS2) and (PromptLow == 0x6C0067006E0045) and (PromptHigh == 0x6800730069) ):		# EFI_HII_SIBT_STRING_UCS2 and "E.n.g.l.i.s.h"
					StringPkgType = ReadList(HiiDbBinListBuff, (HiiDbPointer-0x2B), 1)
					StringOffset = ReadList(HiiDbBinListBuff, (HiiDbPointer-0x26), 4)
					if(StringPkgType == EFI_HII_PACKAGE_STRINGS):
						ReturnAddrDict['StrPkgHdr'] = ((HiiDbPointer + 6) - StringOffset)
		if ( (Guid_LowHalf == 0x697175) and (Parse_Print_Uqi) ):		# compare with "uqi"
			StringHdr = ReadList(HiiDbBinListBuff, (HiiDbPointer+0x4), 1)
			PromptLow = ReadList(HiiDbBinListBuff, (HiiDbPointer+0x5), 6)
			if( (StringHdr == EFI_HII_SIBT_STRING_UCS2) and (PromptLow == 0x6900710075) ):		# EFI_HII_SIBT_STRING_UCS2 and "u.q.i"
				StringPkgType = ReadList(HiiDbBinListBuff, (HiiDbPointer-0x2B), 1)
				StringOffset = ReadList(HiiDbBinListBuff, (HiiDbPointer-0x26), 4)
				if(StringPkgType == EFI_HII_PACKAGE_STRINGS):
					ReturnAddrDict['UqiPkgHdr'] = ((HiiDbPointer + 4) - StringOffset)
		HiiDbPointer = HiiDbPointer + 1
	return ReturnAddrDict


def ParseIfrForms(HiiDbBinListBuff, BiosKnobDict, HiiStrDict, IfrOpHdrAddr, IfrOpHdrEndAddr, BiosFfsFvBase, FfsFilecount, outXml, FrontPageForm, LogFile):
	global TabLevel, PlatInfoMenuDone
	TabLevel = 0
	SetupPgDict = {}
	if(IfrOpHdrEndAddr == 0):
		IfrOpHdrEndAddr = len(HiiDbBinListBuff)
	PrintLog("=========================  Start IFR Forms Parsing  =========================|", LogFile)
	for VarId in BiosKnobDict:
		BiosKnobDict[VarId]['HiiVarId'] = 0xFF

	FormSetCapture = False
	for OpcodeCount in range (0, 0xFFFF):
		if (IfrOpHdrAddr >= IfrOpHdrEndAddr):
			break
		IfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
		if (IfrOpcodesDict.get(IfrOpcode, "N.A.") == "N.A."):
			PrintLog("=========================   End IFR Forms Parsing   =========================|", LogFile)
			break
		IfrOpcodeSize = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
		if ( (IfrOpcode == EFI_IFR_SUPPRESS_IF_OP) or (IfrOpcode == EFI_IFR_GRAY_OUT_IF_OP) ):
			Scope = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
			if(Scope):
				ScopeLvl = 1
			IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
			IfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
			IfrOpcodeSize = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
			Scope = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
			if ( (IfrOpcode == EFI_IFR_TRUE_OP) and (Scope == 0) ):
				while(ScopeLvl):  # go till end of Suppress if TRUE, we need to skip all that stuff
					IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
					IfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
					IfrOpcodeSize = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
					Scope = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
					if(Scope):
						ScopeLvl = ScopeLvl + 1
					if(IfrOpcode == EFI_IFR_END_OP):
						ScopeLvl = ScopeLvl - 1
		if (IfrOpcode == EFI_IFR_FORM_SET_OP):
			FormSetTitle = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x12, 2)
			PrintLog("FormSet = %s  (0x%X)" %(HiiStrDict.get(FormSetTitle), FormSetTitle), LogFile)
			FormSetCapture = True
		if (IfrOpcode == EFI_IFR_FORM_OP):
			CurrentFormId = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
			TitlePrompt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
			if(FormSetCapture):
				FrontPageForm.append(TitlePrompt)
				FormSetCapture = False
			PrintLog("\t\tForm = %s  (0x%X)" %(HiiStrDict.get(TitlePrompt), TitlePrompt), LogFile)
			if(PlatInfoMenuDone == False):
				if(HiiStrDict.get(TitlePrompt) == "Platform Information Menu"):
					outXml.write("\t<%s>\n" %(HiiStrDict.get(TitlePrompt).replace(" ", "_")))
					IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
					ScopeLvl = 1
					for count in range (0, 0x100, 1): # while(endform)
						if(ScopeLvl <= 0):
							PlatInfoMenuDone = True
							outXml.write("\t</%s>\n" %(HiiStrDict.get(TitlePrompt).replace(" ", "_")))
							break
						CurrIfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
						CurrIfrOpcodeSize = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) & 0x7F
						Scope = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr + 0x01), 1) >> 7
						if(Scope):
							ScopeLvl = ScopeLvl + 1
						if(CurrIfrOpcode == EFI_IFR_END_OP):
							ScopeLvl = ScopeLvl - 1
						if(CurrIfrOpcode == EFI_IFR_SUBTITLE_OP):
							Pmpt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
							Hlp = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
							if((HiiStrDict.get(Pmpt, "NF") == "NF") or (HiiStrDict.get(Pmpt, "NF") == "")):
								outXml.write("\n")
							else:
								outXml.write("\t\t<!--%s-->\n" %(HiiStrDict.get(Pmpt, "NF")))
						if(CurrIfrOpcode == EFI_IFR_TEXT_OP):
							Pmpt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
							Hlp = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
							Text2 = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 2)
							if((HiiStrDict.get(Pmpt, "NF") != "NF") and (HiiStrDict.get(Pmpt, "NF") != "")):
								outXml.write("\t\t<!--%s:%s-->\n" %(HiiStrDict.get(Pmpt, "NF"), HiiStrDict.get(Text2, "NF")))
						IfrOpHdrAddr = IfrOpHdrAddr + CurrIfrOpcodeSize
			SetupPgDict[CurrentFormId] = {'Prompt': TitlePrompt, 'PromptList': []}
		if (IfrOpcode == EFI_IFR_REF_OP):
			GotoPrompt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
			PrintLog("\tGotoForm = %s  (0x%X)" %(HiiStrDict.get(GotoPrompt), GotoPrompt), LogFile)
			FormId = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0xD, 2)
			SetupPgDict[CurrentFormId][FormId] = {'Prompt': GotoPrompt}
		if ( (IfrOpcode == EFI_IFR_VARSTORE_OP) or (IfrOpcode == EFI_IFR_VARSTORE_EFI_OP) ):
			if(IfrOpcode == EFI_IFR_VARSTORE_OP):
				VarGuidOffset = 2
				VarIdOffset = 0x12
				VarSizeOffset = 0x14
				VarNameOffset = 0x16
			else:
				VarIdOffset = 2
				VarGuidOffset = 4
				VarSizeOffset = 0x18
				VarNameOffset = 0x1A
			#PrintLog("        CurPtr = 0x%X  IfrOpcodeType = \"%s\" IfrOpcodeSize = 0x%X " %(IfrOpHdrAddr, IfrOpcodesDict.get(IfrOpcode, "N.A."), IfrOpcodeSize), LogFile)
			IfrVarStoreGuid = FetchGuid(HiiDbBinListBuff, (IfrOpHdrAddr+VarGuidOffset))
			IfrVarStoreId = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarIdOffset, 2)
			IfrVarStoreSize = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarSizeOffset, 2)
			IfrVarStoreName = binascii.unhexlify(hex(ReadList(HiiDbBinListBuff, IfrOpHdrAddr+VarNameOffset, (IfrOpcodeSize-VarNameOffset))).strip('L')[2:])[::-1]
			for VarId in BiosKnobDict:
				if ( (BiosKnobDict[VarId]['NvarName'] == IfrVarStoreName) and (BiosKnobDict[VarId]['HiiVarId'] == 0xFF) and ((BiosKnobDict[VarId]['NvarGuid'] == ZeroGuid) or (IfrVarStoreGuid == BiosKnobDict[VarId]['NvarGuid'])) ):
					BiosKnobDict[VarId]['HiiVarId'] = IfrVarStoreId
					BiosKnobDict[VarId]['HiiVarSize'] = IfrVarStoreSize
					break
			#PrintLog("            NvarGuid = \"%s\" " %GuidStr(IfrVarStoreGuid), LogFile)
			#PrintLog("            VarId = 0x%X  NvarSize = 0x%X  NvarName = L\"%s\" " %(IfrVarStoreId, IfrVarStoreSize, IfrVarStoreName), LogFile)
		#PrintLog("        CurPtr = 0x%X  IfrOpcodeType = \"%s\" OffSet = 0x%04X   IfrOpcodeSize = 0x%X " %(IfrOpHdrAddr, IfrOpcodesDict.get(IfrOpcode, "N.A."), ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0A, 2), IfrOpcodeSize), LogFile)
		if ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) or (IfrOpcode == EFI_IFR_CHECKBOX_OP) or (IfrOpcode == EFI_IFR_STRING_OP) ):
			#PrintLog("        CurPtr = 0x%X  IfrOpcodeType = \"%s\" IfrOpcodeSize = 0x%X " %(IfrOpHdrAddr, IfrOpcodesDict.get(IfrOpcode, "N.A."), IfrOpcodeSize), LogFile)
			IfrPrompt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
			IfrHelp = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 2)
			IfrVarId = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+8, 2)
			KnobOffset = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0A, 2)
			SupportedVarFound = False
			for VarIndex in BiosKnobDict:
				if(BiosKnobDict[VarIndex]['HiiVarId'] == IfrVarId):
					CurrIntVarId = VarIndex
					SupportedVarFound = True
					break
			if(SupportedVarFound == False):
				IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
				continue	# not part of supported VarID
			try:
				XmlKnobName = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobName']
			except KeyError:
				XmlKnobName = "NotFound(%d_0x%04X)" %(CurrIntVarId, KnobOffset)
				IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
				continue
			OneOfNumericKnobSz = 0
			CurSetupTypeBin = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['SetupTypeBin']
			if( (CurSetupTypeBin != INVALID_KNOB_SIZE) and (IfrOpcode != CurSetupTypeBin) ):
				IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
				continue
			if ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) ):
				IfrOneOfFlags = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0D, 1)
				OneOfNumericKnobSz = (1 << (IfrOneOfFlags & EFI_IFR_NUMERIC_SIZE))
				CurKnobSzBin = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzBin']
				if( (CurKnobSzBin != INVALID_KNOB_SIZE) and (OneOfNumericKnobSz != CurKnobSzBin) ):
					IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
					continue
			KnobProcessed = BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][0]
			if(KnobProcessed >= 1):
				if(IfrOpcode != BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][1]):
					IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
					continue
				CurKnobInDupList = False
				for DupIndex in sorted(BiosKnobDict[CurrIntVarId]['DupKnobDict']):
					if(XmlKnobName == BiosKnobDict[CurrIntVarId]['DupKnobDict'][DupIndex]['DupKnobName']):
						CurKnobInDupList = True
						break
				if(CurKnobInDupList == False):
					IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
					continue
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Prompt'] = IfrPrompt
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Help'] = IfrHelp
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['SetupTypeHii'] = IfrOpcode
			if(len(SetupPgDict[CurrentFormId]['PromptList']) == 0):
				PromptList = []
				ExitAllLoops = False
				CurFormId = CurrentFormId
				PreviousForms = []
				while(1):
					ProcessCnt = 0
					for FormId in SetupPgDict:
						ProcessCnt = ProcessCnt + 1
						if FormId not in PreviousForms:
							if (SetupPgDict.has_key(FormId)):
								if (SetupPgDict[FormId].has_key(CurFormId)):
									PromptList.append(SetupPgDict[FormId][CurFormId]['Prompt'])
									PreviousForms.append(FormId)
									CurFormId = FormId
									break
						if (ProcessCnt == len(SetupPgDict)):
							PromptList.append(SetupPgDict[CurFormId]['Prompt'])
							if(SetupPgDict[CurFormId]['Prompt'] not in FrontPageForm):
								PromptList.append(0x10000)	# we need to initialize this to "??"
							ExitAllLoops = True
							break
					if(ExitAllLoops):
						break
				SetupPgDict[CurrentFormId]['PromptList'] = PromptList
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['ParentPromptList'] = SetupPgDict[CurrentFormId]['PromptList']
			CurrOpcode = IfrOpcode
			if (IfrOpcode == EFI_IFR_CHECKBOX_OP):
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = 1
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0xD, 1) & 1)
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr+0xD
			elif (IfrOpcode == EFI_IFR_STRING_OP):
				Max = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0E, 1)
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Min'] = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+0x0D, 1)
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Max'] = Max
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = (Max * 2)
				#BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = 
			elif ( (IfrOpcode == EFI_IFR_ONE_OF_OP) or (IfrOpcode == EFI_IFR_NUMERIC_OP) ):
				BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobSzHii'] = OneOfNumericKnobSz
				if(IfrOpcode == EFI_IFR_NUMERIC_OP):
					BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Min'] = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E), OneOfNumericKnobSz)
					BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Max'] = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E+OneOfNumericKnobSz), OneOfNumericKnobSz)
					BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['Step'] = ReadList(HiiDbBinListBuff, (IfrOpHdrAddr+0x0E+OneOfNumericKnobSz+OneOfNumericKnobSz), OneOfNumericKnobSz)
					while (IfrOpcode != EFI_IFR_END_OP):
						if(IfrOpcode == EFI_IFR_DEFAULT_OP):
							NumValSize = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 1) & 0x0F)
							DefValue = 0
							if(NumValSize == EFI_IFR_TYPE_BOOLEAN):
								DefValue = int(ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 1) != 0)
							elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_8):
								DefValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 1)
							elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_16):
								DefValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 2)
							elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_32):
								DefValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 4)
							elif(NumValSize == EFI_IFR_TYPE_NUM_SIZE_64):
								DefValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+5, 8)
							BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = DefValue
							BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr+0x5
						IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
						IfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
						IfrOpcodeSize = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x7F)
				elif(IfrOpcode == EFI_IFR_ONE_OF_OP):
					OneOfScopeLvl = 0
					OneOfScope = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x80) >> 7
					if(OneOfScope):
						OneOfScopeLvl = OneOfScopeLvl + 1
					if(IfrOpcode == EFI_IFR_END_OP):
						OneOfScopeLvl = OneOfScopeLvl - 1
					BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobProcessed] = {}
					BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['FvMainOffHiiDb'] = BiosFfsFvBase+IfrOpHdrAddr
					OptionsCount = 0
					while (OneOfScopeLvl > 0):
						IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
						IfrOpcode = ReadList(HiiDbBinListBuff, IfrOpHdrAddr, 1)
						IfrOpcodeSize = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x7F)
						OneOfScope = (ReadList(HiiDbBinListBuff, IfrOpHdrAddr+1, 1) & 0x80) >> 7
						if(OneOfScope):
							OneOfScopeLvl = OneOfScopeLvl + 1
						if(IfrOpcode == EFI_IFR_END_OP):
							OneOfScopeLvl = OneOfScopeLvl - 1
						if(IfrOpcode == EFI_IFR_ONE_OF_OPTION_OP):
							OptionTextPromt = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+2, 2)
							OptionFlag = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+4, 1)
							OptionTextValSize = (OptionFlag & 0x0F)
							TextValue = 0
							if(OptionTextValSize == EFI_IFR_TYPE_BOOLEAN):
								TextValue = int(ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 1) != 0)
							elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_8):
								TextValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 1)
							elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_16):
								TextValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 2)
							elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_32):
								TextValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 4)
							elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_64):
								TextValue = ReadList(HiiDbBinListBuff, IfrOpHdrAddr+6, 8)
							if( (OptionFlag & EFI_IFR_OPTION_DEFAULT) != 0 ):
								BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['HiiDefVal'] = TextValue
							BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobProcessed][OptionsCount] = { 'OptionText': OptionTextPromt, 'OptionVal':TextValue }
							OptionsCount = OptionsCount + 1
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][0] = (KnobProcessed+1)
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][1] = CurrOpcode
			BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobPrsd'][2] = FfsFilecount
			PrintLog("\t\t\tKnob = %s" %(BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['KnobName']), LogFile)
		IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
	return IfrOpHdrAddr


def ParseIfrStrings(HiiDbBinListBuff=0, StringHdrPtr=0, LogFile=0):
	HiiStringDict = {}
	Prompt = 1
	if(StringHdrPtr == 0):
		return HiiStringDict
	StringPkgSize = ReadList(HiiDbBinListBuff, StringHdrPtr, 3)
	StringOffset = ReadList(HiiDbBinListBuff, (StringHdrPtr+0x8), 4)
	CurrStringPtr = (StringHdrPtr + StringOffset)
	PrintLog("===========    Hii String Package Parsing Start = 0x%X    ==========|" %StringHdrPtr, LogFile)
	while(CurrStringPtr < (StringHdrPtr+StringPkgSize)):
		BlockType = ReadList(HiiDbBinListBuff, (CurrStringPtr), 1)
		CurrStringPtr = CurrStringPtr + 1
		if(BlockType == EFI_HII_SIBT_END):	# end of string block?
			break
		elif(BlockType == EFI_HII_SIBT_STRING_SCSU):
			StrSize = 0
			String = ""
			while(1):
				ChrValue = ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)
				StrSize = StrSize + 1
				if(ChrValue):
					String = String + chr(ChrValue)
				else:
					break
			HiiStringDict[Prompt] = String.replace('<=', ' &lte; ').replace('>=', ' &gte; ').replace('&', 'n').replace('\"', '&quot;').replace('\'', '').replace('\x13', '').replace('\x19', '').replace('\xB5', 'u').replace('\xAE', '').replace('<', ' &lt; ').replace('>', ' &gt; ').replace('\r\n', ' ').replace('\n', ' ')
			Prompt = Prompt + 1
			CurrStringPtr = CurrStringPtr + StrSize
		elif(BlockType == EFI_HII_SIBT_STRING_UCS2):
			StrSize = 0
			String = ""
			while(1):
				ChrValue = ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)
				StrSize = StrSize + 2
				if(ChrValue):
					String = String + chr(ChrValue & 0xFF)
				else:
					break
			HiiStringDict[Prompt] = String.replace('<=', ' &lte; ').replace('>=', ' &gte; ').replace('&', 'n').replace('\"', '&quot;').replace('\'', '').replace('\x13', '').replace('\x19', '').replace('\xB5', 'u').replace('\xAE', '').replace('<', ' &lt; ').replace('>', ' &gt; ').replace('\r\n', ' ').replace('\n', ' ')
			Prompt = Prompt + 1
			CurrStringPtr = CurrStringPtr + StrSize
		elif(BlockType == EFI_HII_SIBT_STRING_SCSU_FONT):
			StrSize = 0
			String = ""
			CurrStringPtr = CurrStringPtr + 1
			while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
				StrSize = StrSize + 1
			CurrStringPtr = CurrStringPtr + StrSize + 1
		elif(BlockType == EFI_HII_SIBT_STRING_UCS2_FONT):
			StrSize = 0
			String = ""
			CurrStringPtr = CurrStringPtr + 1
			while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
				StrSize = StrSize + 2
			CurrStringPtr = CurrStringPtr + StrSize + 2
		elif(BlockType == EFI_HII_SIBT_SKIP1):
			Prompt = Prompt + ReadList(HiiDbBinListBuff, CurrStringPtr, 1)
			CurrStringPtr = CurrStringPtr + 1
		elif(BlockType == EFI_HII_SIBT_SKIP2):
			Prompt = Prompt + ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
			CurrStringPtr = CurrStringPtr + 2
		elif(BlockType == EFI_HII_SIBT_DUPLICATE):
			CurrStringPtr = CurrStringPtr + 2
		elif(BlockType == EFI_HII_SIBT_EXT1):
			CurrStringPtr = CurrStringPtr + 1 + 1
		elif(BlockType == EFI_HII_SIBT_EXT2):
			CurrStringPtr = CurrStringPtr + 1 + 2
		elif(BlockType == EFI_HII_SIBT_EXT4):
			CurrStringPtr = CurrStringPtr + 1 + 4
		elif(BlockType == EFI_HII_SIBT_STRINGS_SCSU):
			StrSize = 0
			StrCount = ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
			CurrStringPtr = CurrStringPtr + 2
			CurStrCnt = 0
			while(CurStrCnt < StrCount):
				while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
					StrSize = StrSize + 1
				StrSize = StrSize + 1
				CurStrCnt = CurStrCnt + 1
			CurrStringPtr = CurrStringPtr + StrSize
		elif(BlockType == EFI_HII_SIBT_STRINGS_SCSU_FONT):
			StrSize = 0
			StrCount = ReadList(HiiDbBinListBuff, CurrStringPtr+1, 2)
			CurrStringPtr = CurrStringPtr + 3
			CurStrCnt = 0
			while(CurStrCnt < StrCount):
				while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 1)):
					StrSize = StrSize + 1
				StrSize = StrSize + 1
				CurStrCnt = CurStrCnt + 1
			CurrStringPtr = CurrStringPtr + StrSize
		elif(BlockType == EFI_HII_SIBT_STRINGS_UCS2):
			StrSize = 0
			StrCount = ReadList(HiiDbBinListBuff, CurrStringPtr, 2)
			CurrStringPtr = CurrStringPtr + 2
			CurStrCnt = 0
			while(CurStrCnt < StrCount):
				while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
					StrSize = StrSize + 2
				StrSize = StrSize + 2
				CurStrCnt = CurStrCnt + 1
			CurrStringPtr = CurrStringPtr + StrSize
		elif(BlockType == EFI_HII_SIBT_STRINGS_UCS2_FONT):
			StrSize = 0
			StrCount = ReadList(HiiDbBinListBuff, CurrStringPtr+1, 2)
			CurrStringPtr = CurrStringPtr + 3
			CurStrCnt = 0
			while(CurStrCnt < StrCount):
				while(ReadList(HiiDbBinListBuff, (CurrStringPtr+StrSize), 2)):
					StrSize = StrSize + 2
				StrSize = StrSize + 2
				CurStrCnt = CurStrCnt + 1
			CurrStringPtr = CurrStringPtr + StrSize
	PrintLog("===========    Hii String Package Parsing End = 0x%X    ==========|" %CurrStringPtr, LogFile)
	return HiiStringDict


def GenerateKnobsSection(BiosKnobDict, HiiStrDict, HiiUqiStrDict, NvRamFvListBuffer, NvramTblDict, outXml, LogFile=0):
# BiosKnobDict[VarId]={'HiiVarId':0xFF, 'KnobDict':{}, 'NvarName':NvarName, 'NvarSize':NvarSize, 'KnobCount':KnobCount}
# BiosKnobDict[VarId]['KnobDict'][KnobOffset] = { 'SetupTypeHii':0, 'KnobName':KnobName, 'KnobSzHii':0, KnobSzBin:0, 'Depex':KnobDepex, 'Prompt':, 'Help':, 'Min':0, 'Max':0, 'Step':0, 'OneOfOptionsDict':{} }
# BiosKnobDict[CurrIntVarId]['KnobDict'][KnobOffset]['OneOfOptionsDict'][OptionsCount] = { 'OptionText':OptionTextPromt, 'OptionVal':TextValue }
# DupKnobDict[DupCount] = { 'DupKnobName':DupKnobName, 'DupDepex':DupKnobDepex }
	for VarCount in sorted(BiosKnobDict):
		#PrintLog("------------------------------------------------------------------------------------------------|", LogFile)
		#PrintLog("======================== ======    VarId = %d    ================================================|" %VarCount, LogFile)
		#PrintLog(" Offset | Sz |  Type    |------------------   Knob Name   -----------|                      Prompt                |  Help  | Depex |", LogFile)
		for KnobOffset in sorted(BiosKnobDict[VarCount]['KnobDict']):
			if(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobPrsd'][0] == 0):
				continue	# Skip current Iteration, since current entry was not processed by IFR parser.
			CurSetupType = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['SetupTypeHii']
			CurKnobName  = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobName']
			CurKnobSize  = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobSzHii']
			CurDepex     = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Depex']
			CurSetupTypeStr = SetupTypeHiiDict.get(CurSetupType, "Unknown")
			if( CurSetupTypeStr == "Unknown" ):
				continue	# don't publish unsupported Setup Type
			if(CurSetupType == EFI_IFR_ONE_OF_OP):
				if(len(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict']) > 1):
					CurDepex = "TRUE"
			IfrPrompt = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Prompt']
			IfrHelp = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Help']
			HiiDefVal = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['HiiDefVal'] 
			PromptList = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['ParentPromptList']
			SetupPgPtr = HiiStrDict.get(IfrPrompt, "N.A.")
			DefaultVal = HiiDefVal
			for cnt in range (0, len(PromptList)):
				SetupPgPtr = HiiStrDict.get(PromptList[cnt], "???") + '/' + SetupPgPtr
			if(len(NvramTblDict)):
				try:
					CurrentVal = ReadList(NvRamFvListBuffer, (NvramTblDict[VarCount]['NvarDataBufPtr']+KnobOffset), CurKnobSize)
				except KeyError:
					CurrentVal = HiiDefVal
			else:
				CurrentVal = HiiDefVal
			#PrintLog("--------|----|----------|--------------------------------------------|--------------------------------------------|-----------------------------", LogFile)
			#PrintLog(" 0x%04X | %d  | %8s | %42s | %42s | %s | %s |" %(KnobOffset, CurKnobSize, CurSetupTypeStr, BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['KnobName'], HiiStrDict.get(IfrPrompt, "NotFound(0x%04X)" %IfrPrompt), HiiStrDict.get(IfrHelp, "NotFound(0x%04X)" %IfrHelp), BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Depex']), LogFile)
			if (HiiUqiStrDict == {}):
				outXml.write("\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" prompt=\"%s\" description=\"%s\" size=\"%d\" offset=\"0x%04X\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\"" %(CurSetupTypeStr, CurKnobName, VarCount, HiiStrDict.get(IfrPrompt, "NotFound(0x%04X)" %IfrPrompt), HiiStrDict.get(IfrHelp, "NotFound(0x%04X)" %IfrHelp), CurKnobSize, KnobOffset, CurDepex, SetupPgPtr, (CurKnobSize*2), DefaultVal, (CurKnobSize*2), CurrentVal))
			else:
				outXml.write("\t\t<knob setupType=\"%s\" name=\"%s\" varstoreIndex=\"%02d\" prompt=\"%s\" description=\"%s\" UqiVal=\"%s\" size=\"%d\" offset=\"0x%04X\" depex=\"%s\" SetupPgPtr = \"%s\" default=\"0x%0*X\" CurrentVal=\"0x%0*X\"" %(CurSetupTypeStr, CurKnobName, VarCount, HiiStrDict.get(IfrPrompt, "NotFound(0x%04X)" %IfrPrompt), HiiStrDict.get(IfrHelp, "NotFound(0x%04X)" %IfrHelp), HiiUqiStrDict.get(IfrPrompt, ""), CurKnobSize, KnobOffset, CurDepex, SetupPgPtr, (CurKnobSize*2), DefaultVal, (CurKnobSize*2), CurrentVal))
			if(CurSetupType == EFI_IFR_ONE_OF_OP):
				outXml.write(">\n")
				KnobInstances = len(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'])
				for KnobPrsCnt in range (0, KnobInstances):
					#PrintLog("        |    |          |                                            |---------  Option Text  Set = %d ------------|----Option Value ---|" %KnobPrsCnt, LogFile)
					PrintOptionList = False
					if( KnobInstances > 1 ):
						FoundInstance = 1
						if(KnobPrsCnt == 0):
							outXml.write("\t\t\t<options depex=\"%s\">\n" %BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Depex'])
							PrintOptionList = True
						else:
							for DupIndex in sorted(BiosKnobDict[VarCount]['DupKnobDict']):
								if(CurKnobName == BiosKnobDict[VarCount]['DupKnobDict'][DupIndex]['DupKnobName']):
									if(KnobPrsCnt == FoundInstance):
										outXml.write("\t\t\t<options depex=\"%s\">\n" %BiosKnobDict[VarCount]['DupKnobDict'][DupIndex]['DupDepex'])
										PrintOptionList = True
										break
									FoundInstance = FoundInstance + 1
					else:
						outXml.write("\t\t\t<options>\n")
						PrintOptionList = True
					if (PrintOptionList):
						for OptionCount in sorted(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt]):
							OptionText = BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt][OptionCount]['OptionText']
							#PrintLog("        |    |          |                                            | %42s | 0x%-16X |" %(HiiStrDict.get(OptionText, "NotFound(0x%04X)" %OptionText), BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt][OptionCount]['OptionVal']), LogFile)
							outXml.write("\t\t\t\t<option text=\"%s\" value=\"0x%X\"/>\n" %(HiiStrDict.get(OptionText, "NotFound(0x%04X)" %OptionText), BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['OneOfOptionsDict'][KnobPrsCnt][OptionCount]['OptionVal']))
						outXml.write("\t\t\t</options>\n")
				outXml.write("\t\t</knob>\n")
			elif(CurSetupType == EFI_IFR_NUMERIC_OP):
				#PrintLog("        |    |          |                                            | Min = 0x%X  Max = 0x%X  Step = 0x%X |" %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Step']), LogFile)
				outXml.write(" min=\"0x%X\" max=\"0x%X\" step=\"%d\"/>\n" %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Step']))
			elif(CurSetupType == EFI_IFR_STRING_OP):
				#PrintLog("        |    |          |                                            | MinSize = 0x%X  MaxSize = 0x%X |" %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max']), LogFile)
				outXml.write(" minsize=\"0x%X\" maxsize=\"0x%X\"/>\n" %(BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Min'], BiosKnobDict[VarCount]['KnobDict'][KnobOffset]['Max']))
			elif(CurSetupType == EFI_IFR_CHECKBOX_OP):
				outXml.write("/>\n")
			else:
				outXml.write("/>\n")

def FetchBiosId(BiosIdFfsFile, PcBiosId=False):
	BiosIdFile = open(BiosIdFfsFile, "rb")
	BiosIdListBuff = list(BiosIdFile.read())
	BiosIdFile.close()
	FfsSize = ReadList(BiosIdListBuff, 0x14, 3)
	BiosIdString = ""
	CharSz = 2
	CharStart = 0x24
	if(PcBiosId):
		CharSz = 1
		CharStart = 0x1C
	if (FfsSize < 0x100):
		for count in range (0, 100):
			ChrVal = ReadList(BiosIdListBuff, (CharStart+(count*CharSz)), 1)
			if(ChrVal == 0):
				break
			BiosIdString = BiosIdString + chr(ChrVal)
	else:
		BiosIdString = "Unknown"
	return BiosIdString

def ReplOneOfDefFlag(DbBinListBuffer, IfrOpHdrAddr, ReqValue):
		IfrOpcodeSize = (ReadList(DbBinListBuffer, IfrOpHdrAddr+1, 1) & 0x7F)
		CurIfrOpcode = ReadList(DbBinListBuffer, IfrOpHdrAddr, 1)
		while (CurIfrOpcode != EFI_IFR_END_OP):
			if(CurIfrOpcode == EFI_IFR_ONE_OF_OPTION_OP):
				OptionFlag = ReadList(DbBinListBuffer, IfrOpHdrAddr+4, 1)
				OptionTextValSize = (OptionFlag & 0x0F)
				OneOfDefVal = 0
				NewOptionFlag = 0
				if(OptionTextValSize == EFI_IFR_TYPE_BOOLEAN):
					OneOfDefVal = int(ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 1) != 0)
				elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_8):
					OneOfDefVal = ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 1)
				elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_16):
					OneOfDefVal = ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 2)
				elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_32):
					OneOfDefVal = ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 4)
				elif(OptionTextValSize == EFI_IFR_TYPE_NUM_SIZE_64):
					OneOfDefVal = ReadList(DbBinListBuffer, IfrOpHdrAddr+6, 8)
				if(ReqValue == OneOfDefVal):
					NewOptionFlag = (OptionFlag|EFI_IFR_OPTION_DEFAULT | EFI_IFR_OPTION_DEFAULT_MFG)
				else:
					NewOptionFlag = (OptionFlag & (~(EFI_IFR_OPTION_DEFAULT | EFI_IFR_OPTION_DEFAULT_MFG) & 0xFF))
				WriteList(DbBinListBuffer, IfrOpHdrAddr+4, 1, NewOptionFlag)
			IfrOpHdrAddr = IfrOpHdrAddr + IfrOpcodeSize
			IfrOpcodeSize = (ReadList(DbBinListBuffer, IfrOpHdrAddr+1, 1) & 0x7F)
			CurIfrOpcode = ReadList(DbBinListBuffer, IfrOpHdrAddr, 1)

FileGuidListtoSave  = [ gNvRamFvGuid, gDxePlatformFfsGuid, gBiosKnobsDataBinGuid, gSocketSetupDriverFfsGuid, gSvSetupDriverFfsGuid, gFpgaDriverFfsGuid, gEfiBiosIdGuid, gCpPcBiosIdFileGuid, gDefaultDataOptSizeFileGuid, gDefaultDataFileGuid, gVpdGuid, gClientSetupFfsGuid, gClientTestMenuSetupFfsGuid, gPcGenSetupDriverFfsGuid, gEmulationDriverFfsGuid, gMerlinXAppGuid ]
SetupDriverGuidList = [ gDxePlatformFfsGuid, gSocketSetupDriverFfsGuid, gSvSetupDriverFfsGuid, gFpgaDriverFfsGuid, gClientSetupFfsGuid, gClientTestMenuSetupFfsGuid , gPcGenSetupDriverFfsGuid, gEmulationDriverFfsGuid ]

def GetsetBiosKnobsFromBin(BiosBinaryFile=0, BiosOutSufix=0, Operation="genxml", XmlFilename=0, IniFile=0, UpdateHiiDbDef=False, BiosOut="", KnobsStrList=[]):
	global FileGuidListDict, FileSystemSaveCount, FwpPrintEn, FwIngrediantDict, SaveFvMainFile, FvMainCompDict, FvMainCount, PlatInfoMenuDone
	clb.LastErrorSig = 0x0000
	FileGuidListDict = {}
	FvMainCompDict = {}
	FileSystemSaveCount = 0
	FvMainCount = 0
	LogFile = open(PrintLogFile, "w")
	clb.OutBinFile = ""
	DelTempFvFfsFiles(clb.TempFolder)

	BiosBinFile = open(BiosBinaryFile, "rb")
	BiosBinListBuff = list(BiosBinFile.read())
	BiosBinFile.close()
	FetchFwIngrediantInfo(BiosBinListBuff, False)
	if (FwIngrediantDict['FlashDescpValid'] != 0):
		BiosRegionBase = FwIngrediantDict['FlashRegions'][BIOS_Region]['BaseAddr']
		BiosEnd = FwIngrediantDict['FlashRegions'][BIOS_Region]['EndAddr'] + 1
	else:
		BiosRegionBase = 0
		BiosEnd = len(BiosBinListBuff)

	if( (Operation == "prog") and (UpdateHiiDbDef) ):
		SaveFvMainFile = True
	ProcessBin(BiosBinListBuff, BiosRegionBase, FileGuidListtoSave, LogFile, BiosRegionEnd=BiosEnd)
	BiosIDFile = clb.TempFolder+os.sep+"%X_File.ffs" %gEfiBiosIdGuid[0]
	FoundPcBuild = False
	if(os.path.isfile(BiosIDFile)):
		BiosIdString = FetchBiosId(clb.TempFolder+os.sep+"%X_File.ffs" %gEfiBiosIdGuid[0])
	else:
		FoundPcBuild = True
		BiosIdString = FetchBiosId(clb.TempFolder+os.sep+"%X_File.ffs" %gCpPcBiosIdFileGuid[0], True)
	BiosKnobDict = BiosKnobsDataBinParser(clb.TempFolder+os.sep+"%X_File.ffs" %gBiosKnobsDataBinGuid[0], BiosIdString)

	NvRamFileName = clb.TempFolder+os.sep+"%X_File.fv" %gNvRamFvGuid[0]
	NvRamFile = open(NvRamFileName, "rb")
	NvRamFvListBuffer = []
	NvRamFvListBuffer = list(NvRamFile.read())
	NvRamFile.close()
	NvRamDefDataFileGuid = gNvRamFvGuid 
	NvramTblDict = ParseNvram(NvRamFvListBuffer, BiosKnobDict, 0x48, LogFile)
	if(len(NvramTblDict) == 0):
		NvRamFileName = clb.TempFolder+os.sep+"%X_File.ffs" %gDefaultDataOptSizeFileGuid[0]
		NvRamDefDataFileGuid = gDefaultDataOptSizeFileGuid
		if (os.path.isfile(NvRamFileName) == False):
			NvRamFileName = clb.TempFolder+os.sep+"%X_File.ffs" %gDefaultDataFileGuid[0]
			NvRamDefDataFileGuid = gDefaultDataFileGuid
		if (os.path.isfile(NvRamFileName) == False):
			NvRamFileName = clb.TempFolder+os.sep+"%X_File.ffs" %gVpdGuid[0]
			NvRamDefDataFileGuid = gVpdGuid
		if (os.path.isfile(NvRamFileName)):
			NvRamFile = open(NvRamFileName, "rb")
			NvRamFvListBuffer = []
			NvRamDefDataFileDict = {}
			NvRamFvListBuffer = list(NvRamFile.read())
			NvRamFile.close()
			NvramTblDict = ParseNvram(NvRamFvListBuffer, BiosKnobDict, 0, LogFile)

	print " Fetching Firmware Info from the given Bios Binary..."
	if (XmlFilename == 0):
		XmlFilename = clb.TempFolder +os.sep+'%s_FwInfo.xml' %BiosIdString
	outXml = open(XmlFilename,'w')
	outXml.write("<SYSTEM>\n")
	outXml.write("\t<PLATFORM NAME=\"Generated by XmlCli ToolKit - PythonSv.misc.XmlCli.UefiFwParser.py\"/>\n")
	BiosIdLst = BiosIdString.split('.')
	BiosDate = BiosIdLst[len(BiosIdLst)-1]
	if(FoundPcBuild):
		outXml.write("\t<BIOS VERSION=\"%s\" TSTAMP=\"%s.%s.%s at %s:%s Hrs\"/>\n" %(BiosIdString, BiosDate[0:2], BiosDate[2:4], BiosDate[4:8], BiosDate[8:10], BiosDate[10:12]))
	else:
		outXml.write("\t<BIOS VERSION=\"%s\" TSTAMP=\"%s.%s.%s at %s:%s Hrs\"/>\n" %(BiosIdString, BiosDate[2:4], BiosDate[4:6], '20'+BiosDate[0:2], BiosDate[6:8], BiosDate[8:10]))
	outXml.write("\t<GBT Version=\"3.0002\" TSTAMP=\"March 26 2013\" Type=\"Offline\"/>\n")

	if (FwIngrediantDict['FlashDescpValid'] != 0):
		outXml.write("\t<FlashRegions>\n")
		for Entry in sorted(FwIngrediantDict['FlashRegions']):
			if(FwIngrediantDict['FlashRegions'][Entry]['BaseAddr'] == FwIngrediantDict['FlashRegions'][Entry]['EndAddr']):
				continue
			outXml.write("\t\t<Region Name=\"%s\" Base=\"0x%08X\" End=\"0x%08X\"/>\n" %(FwIngrediantDict['FlashRegions'][Entry]['Name'], FwIngrediantDict['FlashRegions'][Entry]['BaseAddr'], FwIngrediantDict['FlashRegions'][Entry]['EndAddr']))
		outXml.write("\t</FlashRegions>\n")
		if(len(FwIngrediantDict['ME']) != 0):
			outXml.write("\t<ME Version=\"%s\" TSTAMP=\"%s\" Type=\"%s\"/>\n" %(FwIngrediantDict['ME']['Version'], FwIngrediantDict['ME']['Date'], FwIngrediantDict['ME']['Type']))
	outXml.write("\t<PchStrapsBlock FlashDescriptorValid=\"%d\">\n" %(FwIngrediantDict['FlashDescpValid']))
	if (FwIngrediantDict['FlashDescpValid'] != 0):
		for StrapNo in sorted(FwIngrediantDict['PCH_STRAPS']):
			outXml.write("\t\t<Strap Number=\"%02d\" Value=\"0x%08X\"/>\n" %(StrapNo, FwIngrediantDict['PCH_STRAPS'][StrapNo]))
	outXml.write("\t</PchStrapsBlock>\n")

	outXml.write("\t<FIT>\n")
	for Entry in sorted(FwIngrediantDict['FIT']):
		import XmlCli as cli
		if(FwIngrediantDict['FIT'][Entry]['Type'] == cli.FIT_TBL_ENTRY_TYPE_0):
			continue
		outXml.write("\t\t<Entry Name=\"%s\" Type=\"%d\" Address=\"0x%X\" Size=\"0x%X\"/>\n" %(FwIngrediantDict['FIT'][Entry]['Name'], FwIngrediantDict['FIT'][Entry]['Type'], FwIngrediantDict['FIT'][Entry]['Address'], FwIngrediantDict['FIT'][Entry]['Size']))
	outXml.write("\t</FIT>\n")
	if (FwIngrediantDict['FlashDescpValid'] != 0):
		if(len(FwIngrediantDict['ACM']) != 0):
			outXml.write("\t<ACM Version=\"%s\" TSTAMP=\"%s\" Type=\"%s\" VendorId=\"0x%X\"/>\n" %(FwIngrediantDict['ACM']['Version'], FwIngrediantDict['ACM']['Date'], FwIngrediantDict['ACM']['Type'], FwIngrediantDict['ACM']['VendorId']))
	outXml.write("\t<UcodeEntries>\n")
	for Entry in sorted(FwIngrediantDict['Ucode']):
		outXml.write("\t\t<Ucode CpuId=\"0x%X\" Version=\"0x%08X\" TSTAMP=\"%s\" Size=\"0x%X\"/>\n" %(FwIngrediantDict['Ucode'][Entry]['CpuId'], FwIngrediantDict['Ucode'][Entry]['Version'], FwIngrediantDict['Ucode'][Entry]['Date'], FwIngrediantDict['Ucode'][Entry]['UcodeSize']))
	outXml.write("\t</UcodeEntries>\n")
	BiosBinParseCount = 0
	BiosDictArray = {}
	KnobStartTag = False
	FrontPageForm = []
	for count in range (0, len(SetupDriverGuidList)):
		CurFfsFileName = clb.TempFolder+os.sep+"%X_File.ffs" %SetupDriverGuidList[count][0]
		if (os.path.isfile(CurFfsFileName) == False):
			continue	# didnt found this file, maybe unsupported driver for following binary
		if(BiosBinParseCount):
			BiosKnobDict = BiosKnobsDataBinParser(clb.TempFolder+os.sep+"%X_File.ffs" %gBiosKnobsDataBinGuid[0], BiosIdString)
		BiosBinParseCount = BiosBinParseCount + 1
		HiiDbBinFile = open(CurFfsFileName, "rb")
		HiiDbBinListBuff = list(HiiDbBinFile.read())
		HiiDbBinFile.close()
		PrintLog("=============== Now Parsing %s binary ================|" %(clb.TempFolder+os.sep+"%X_File.ffs" %SetupDriverGuidList[count][0]), LogFile)
		HiiPkgAddrDict = GetIfrFormsHdr(HiiDbBinListBuff)
		for FileCountId in FileGuidListDict:
			if(FileGuidListDict[FileCountId]['FileGuid'] == SetupDriverGuidList[count]):
				BiosFfsFvBase = FileGuidListDict[FileCountId]['BiosBinPointer']
				break
		PlatInfoMenuDone = False
		StringHdrPtr = HiiPkgAddrDict['StrPkgHdr']
		HiiStrDict = ParseIfrStrings(HiiDbBinListBuff, StringHdrPtr, LogFile)
		HiiUqiStrDict = {}
		if(Parse_Print_Uqi):
			HiiUqiStrDict = ParseIfrStrings(HiiDbBinListBuff, HiiPkgAddrDict['UqiPkgHdr'], LogFile)
		for IfrFormPkgCount in range (0, (len(HiiPkgAddrDict['IfrList']))):
			IfrOpHdrAddr = ParseIfrForms(HiiDbBinListBuff, BiosKnobDict, HiiStrDict, HiiPkgAddrDict['IfrList'][IfrFormPkgCount], 0, BiosFfsFvBase, count, outXml, FrontPageForm, LogFile)
		PrintLog("======  Overall End of IFR parsing for Setup Driver count No: %d  ==============" %(count), LogFile)
		if(KnobStartTag == False):
			outXml.write("\t<biosknobs>\n")
			KnobStartTag = True
		GenerateKnobsSection(BiosKnobDict, HiiStrDict, HiiUqiStrDict, NvRamFvListBuffer, NvramTblDict, outXml, LogFile)
		BiosDictArray[count] = BiosKnobDict
	if(KnobStartTag):
		outXml.write("\t</biosknobs>\n")
	outXml.write("</SYSTEM>\n")
	outXml.close()
	clb.SanitizeXml(XmlFilename)
	print " Fetching Firmware Info Done in %s " %XmlFilename

	if( (Operation == "prog") or (Operation == "readonly") ):
		tmpPrintSts = FwpPrintEn
		FwpPrintEn = True
		ProgBinfileName=os.sep.join([clb.TempFolder, "biosKnobsdata.bin"])
		if(IniFile == 0):
			if(len(KnobsStrList) != 0):
				IniFilePart = open(clb.TmpKnobsIniFile, "w")
				IniFilePart.write(";-----------------------------------------------------------------\n")
				IniFilePart.write("; FID XmlCli contact: amol.shinde@intel.com\n")
				IniFilePart.write("; XML Shared MailBox settings for XmlCli based setup\n")
				IniFilePart.write("; The name entry here should be identical as the name from the XML file (retain the case)\n")
				IniFilePart.write(";-----------------------------------------------------------------\n")
				IniFilePart.write("[BiosKnobs]\n")
				for KnobString in KnobsStrList:
					IniFilePart.write("%s\n" %KnobString)
				IniFilePart.close()
				IniFile = clb.TmpKnobsIniFile
			else:
				IniFile = os.sep.join([clb.XmlCliPath, "cfg"+os.sep+"BiosKnobs.ini"])
		if(clb.FlexConCfgFile):
			prs.GenBiosKnobsIni(XmlFilename, IniFile, clb.TmpKnobsIniFile)
			IniFile = clb.TmpKnobsIniFile
		TmpBuff = prs.parseCliinixml(XmlFilename, IniFile, ProgBinfileName)
		if(len(TmpBuff) == 0):
			print "Aborting due to Error!"
			FwpPrintEn = tmpPrintSts
			if( (Operation == "prog") and (UpdateHiiDbDef) ):
				SaveFvMainFile = False
			DelTempFvFfsFiles(clb.TempFolder)
			FileGuidListDict = {}
			FileSystemSaveCount = 0
			LogFile.close()
			clb.LastErrorSig = 0xFE91	# GetsetBiosKnobsFromBin: Empty Input Knob List
			return 1
		ProgBinfile = open(ProgBinfileName, "rb")
		KnobsProgListBuff = list(ProgBinfile.read())
		ProgBinfile.close()
		NvRamUpdateFlag = 0
		BiosKnobUpdate = 0
		PrintLog(" see below for the results..", LogFile)
		if(UpdateHiiDbDef):
			PrintLog("|--|----|----------------------------------------|--|-----------|-----------|-----------|", LogFile)
			PrintLog("|VI|Ofst|                 Knob Name              |Sz| OrgDefVal | NewDefVal |   CurVal  |", LogFile)
			PrintLog("|--|----|----------------------------------------|--|-----------|-----------|-----------|", LogFile)
		else:
			PrintLog("|--|----|----------------------------------------|--|-----------|-----------|", LogFile)
			PrintLog("|VI|Ofst|                 Knob Name              |Sz|   DefVal  |   CurVal  |", LogFile)
			PrintLog("|--|----|----------------------------------------|--|-----------|-----------|", LogFile)

		for DriverFilecount in range (0, len(SetupDriverGuidList)):
			FvMainUpdateFlag = 0
			FvMainListBuffer = []
			CurFfsFileName = clb.TempFolder+os.sep+"%X_File.ffs" %SetupDriverGuidList[DriverFilecount][0]
			if (os.path.isfile(CurFfsFileName) == False):
				continue	# didnt found this file, maybe unsupported driver for following binary

			if( (Operation == "prog") and (UpdateHiiDbDef) ):
				UpdateBiosBinDirectly = False
				FileFound = False
				for CurrFileCount in FileGuidListDict:
					if (SetupDriverGuidList[DriverFilecount] == FileGuidListDict[CurrFileCount]['FileGuid']):
						TmpFileName =  FvMainFileName.replace('FvMain_0.fv', 'FvMain_%d.fv' %FileGuidListDict[CurrFileCount]['FvMainCount'])
						if(os.path.isfile(TmpFileName) and FileGuidListDict[CurrFileCount]['IsCmprFv']):
							TmpFile = open(TmpFileName, 'rb')
							FvMainListBuffer = list(TmpFile.read())
							TmpFile.close()
						else:
							UpdateBiosBinDirectly = True
						FileFound = True
						break
				if(FileFound == False):
					print "Print Did not find the desired Setup Driver GUID in current file (%s)" %CurFfsFileName
					continue
			if( (Operation == "prog") or (Operation == "readonly") ):
				if(len(KnobsProgListBuff) > 8):
					EntryCount = ReadList(KnobsProgListBuff, 0, 4)
					KnobBinPtr = 0x4
					for Count in range (0, EntryCount):
						VarStore = ReadList(KnobsProgListBuff, KnobBinPtr, 1)
						Offset = ReadList(KnobsProgListBuff, KnobBinPtr+1, 2)
						KnobSize = ReadList(KnobsProgListBuff, KnobBinPtr+3, 1)
						ReqValue = ReadList(KnobsProgListBuff, KnobBinPtr+4, KnobSize)
						if( (Offset < BiosDictArray[DriverFilecount][VarStore]['HiiVarSize']) and (BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['KnobPrsd'][2] == DriverFilecount) ):
							HiiDefVal = BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['HiiDefVal']
							if(len(NvramTblDict)):
								CurValue = ReadList(NvRamFvListBuffer, (NvramTblDict[VarStore]['NvarDataBufPtr']+Offset), KnobSize)
							else:
								CurValue = HiiDefVal
							DefVal = HiiDefVal

							if(Operation != "readonly"):
								if( (CurValue != ReqValue) and (len(NvramTblDict)) ):
									WriteList(NvRamFvListBuffer, (NvramTblDict[VarStore]['NvarDataBufPtr']+Offset), KnobSize, ReqValue)
									NvRamUpdateFlag = NvRamUpdateFlag + 1
								if( (HiiDefVal != ReqValue) and (UpdateHiiDbDef) ):
									SetupTypeHii = BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['SetupTypeHii']
									if( (SetupTypeHii == EFI_IFR_CHECKBOX_OP) or (SetupTypeHii == EFI_IFR_NUMERIC_OP)):
										if(UpdateBiosBinDirectly):
											WriteList(BiosBinListBuff, BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['FvMainOffHiiDb'], KnobSize, ReqValue)
										else:
											WriteList(FvMainListBuffer, FvMainCompDict[FileGuidListDict[CurrFileCount]['FvMainCount']]['UcomprsSecSizeOffset']+ BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['FvMainOffHiiDb'], KnobSize, ReqValue)
											FvMainUpdateFlag = FvMainUpdateFlag + 1
										BiosKnobUpdate = BiosKnobUpdate + 1
									elif(SetupTypeHii == EFI_IFR_ONE_OF_OP):
										if(UpdateBiosBinDirectly):
											IfrOpHdrAddr = BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['FvMainOffHiiDb']
											ReplOneOfDefFlag(BiosBinListBuff, IfrOpHdrAddr, ReqValue)
										else:
											IfrOpHdrAddr = FvMainCompDict[FileGuidListDict[CurrFileCount]['FvMainCount']]['UcomprsSecSizeOffset']+BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['FvMainOffHiiDb']
											ReplOneOfDefFlag(FvMainListBuffer, IfrOpHdrAddr, ReqValue)
											FvMainUpdateFlag = FvMainUpdateFlag + 1
										BiosKnobUpdate = BiosKnobUpdate + 1
							else:
								ReqValue = CurValue
							KnobName = BiosDictArray[DriverFilecount][VarStore]['KnobDict'][Offset]['KnobName']
							if(UpdateHiiDbDef):
								PrintLog("|%2X|%4X|%40s|%2X| %8X  | %8X  | %8X  |" %(VarStore, Offset, KnobName, KnobSize, DefVal, ReqValue, ReqValue), LogFile)
								PrintLog("|--|----|----------------------------------------|--|-----------|-----------|-----------|", LogFile)
							else:
								PrintLog("|%2X|%4X|%40s|%2X| %8X  | %8X  |" %(VarStore, Offset, KnobName, KnobSize, DefVal, ReqValue), LogFile)
								PrintLog("|--|----|----------------------------------------|--|-----------|-----------|", LogFile)
						KnobBinPtr = KnobBinPtr + 4 + KnobSize
					if( ReadList(KnobsProgListBuff, KnobBinPtr, 4) != 0xE9D0FBF4):
						PrintLog("error parsing KnobsProgListBuff", LogFile)
			if(FvMainUpdateFlag != 0):
				TmpFileName =  FvMainFileName.replace('FvMain_0.fv', 'FvMain_%d_New.fv' %FileGuidListDict[CurrFileCount]['FvMainCount'])
				if(os.path.isfile(TmpFileName)):
					clb.RemoveFile(TmpFileName)
				ModFvBinFile = open(TmpFileName, "wb")
				ModFvBinFile.write(string.join(FvMainListBuffer, ''))
				ModFvBinFile.close()
		CreateOutFile = False
		if( (NvRamUpdateFlag != 0) or (BiosKnobUpdate != 0) ):
			if(NvRamUpdateFlag != 0):
				for FileCountId in FileGuidListDict:
					if(FileGuidListDict[FileCountId]['FileGuid'] == NvRamDefDataFileGuid):
						BiosBinBase = FileGuidListDict[FileCountId]['BiosBinPointer']
						FileSystemSz = FileGuidListDict[FileCountId]['FileSystemSize']
						BiosBinListBuff[BiosBinBase: (BiosBinBase+FileSystemSz)] = NvRamFvListBuffer[0:FileSystemSz]
						break
			UpdateFvMainComp(BiosBinListBuff)
			CreateOutFile = True
		else:
			PrintLog ("No Changes detected/applied", LogFile)
			if((Operation == "prog") and ForceOutFile):
				PrintLog ("ForceOutFile variable enabled, Preparing to Copy the binary to out folder anyways", LogFile)
				CreateOutFile = True
		if(CreateOutFile):
			BiosFileName, BiosFileExt = os.path.splitext(os.path.basename(BiosBinaryFile))
			NewBiosFileName = BiosFileName.replace(BiosIdString, "Found")
			if(NewBiosFileName == BiosFileName):
				NewBiosFileName = BiosFileName + "_" + BiosIdString
			else:
				NewBiosFileName = BiosFileName
			BiosOutFolder = clb.TempFolder
			ModBiosBinFileName = ""
			if(BiosOut != ""):
				if(os.path.lexists(BiosOut)):
					BiosOutFolder = BiosOut
				elif(os.path.isdir(os.path.dirname(BiosOut))):
					ModBiosBinFileName = BiosOut
			if(ModBiosBinFileName == ""):
				if(BiosOutSufix == 0):
					ModBiosBinFileName = BiosOutFolder+os.sep+"%s_New%s" %(NewBiosFileName, BiosFileExt)
				else:
					ModBiosBinFileName = BiosOutFolder+os.sep+"%s_%s%s" %(NewBiosFileName, BiosOutSufix, BiosFileExt)
			clb.OutBinFile = ModBiosBinFileName
			ModBiosBinFile = open(ModBiosBinFileName, "wb")
			ModBiosBinFile.write(string.join(BiosBinListBuff, ''))
			ModBiosBinFile.close()
			PrintLog ("Created New updated Bios File %s with desired knob settings" %ModBiosBinFileName, LogFile)
		FwpPrintEn = tmpPrintSts

	if( (Operation == "prog") and (UpdateHiiDbDef) ):
		SaveFvMainFile = False

	DelTempFvFfsFiles(clb.TempFolder)
	FileGuidListDict = {}
	FileSystemSaveCount = 0
	LogFile.close()
	return 0

def FlashRegionInfo(UefiFwBinListBuff, PrintEn=True):
	global FwIngrediantDict
	clb.LastErrorSig = 0x0000
	FwIngrediantDict['FlashRegions']={}
	FwIngrediantDict['FlashDescpValid'] = 0
	DescBase = 0x00
	FlashValSig = clb.ReadList(UefiFwBinListBuff, (DescBase+0x10), 4)
	if(FlashValSig != 0x0FF0A55A):
		print "Invalid Falsh descriptor section!"
		FwIngrediantDict['FlashDescpValid'] = 0
		clb.LastErrorSig = 0x1FD4	# FlashRegionInfo: Invalid Falsh descriptor section
		return 1
	FwIngrediantDict['FlashDescpValid'] = 1
	FlashRegBaseOfst = (clb.ReadList(UefiFwBinListBuff, (DescBase+0x16), 1) << 4)
	NoOfRegions = ((clb.ReadList(UefiFwBinListBuff, (DescBase+0x17), 1) & 0x7) + 1)
	if(NoOfRegions < 7):
		NoOfRegions = 7		# temp patch, as some binaries dont have this set correctly.
	for region in range (0, NoOfRegions):
		RegBase  = (clb.ReadList(UefiFwBinListBuff, (DescBase+FlashRegBaseOfst+(region*4)+0), 2) & 0x7FFF)
		RegLimit = (clb.ReadList(UefiFwBinListBuff, (DescBase+FlashRegBaseOfst+(region*4)+2), 2) & 0x7FFF)
		if( (RegBase == 0x7FFF) or (RegLimit == 0) ):
			if PrintEn:
				print "Unused or Invalid Region (%d)" %region
			FwIngrediantDict['FlashRegions'][region] = {'Name': FlashRegionDict[region], 'BaseAddr': 0xFFFFFFFF, 'EndAddr': 0xFFFFFFFF}
			continue
		FwIngrediantDict['FlashRegions'][region] = {'Name': FlashRegionDict[region], 'BaseAddr': (RegBase << 12), 'EndAddr': ((RegLimit << 12) | 0xFFF)}
	if PrintEn:
		print "|--------|------------------|------------|------------|"
		print "| Region |   Region Name    |  BaseAddr  |  End Addr  |"
		print "|--------|------------------|------------|------------|"
	for FlashRegion in FwIngrediantDict['FlashRegions']:
		if PrintEn:
			print "|   %d    | %-16s | 0x%-8X | 0x%-8X |" %(FlashRegion, FlashRegionDict[FlashRegion], FwIngrediantDict['FlashRegions'][FlashRegion]['BaseAddr'], FwIngrediantDict['FlashRegions'][FlashRegion]['EndAddr'])
	if PrintEn:
		print "|--------|------------------|------------|------------|"
	return 0

def GetMeInfo(UefiFwBinListBuff, PrintEn=True):
	global FwIngrediantDict
	FwIngrediantDict['ME']={}
	MeBase = FwIngrediantDict['FlashRegions'][ME_Region]['BaseAddr']
	if((MeBase >= len(UefiFwBinListBuff)) or (MeBase == 0) ):
		return
	FPT_Sig = clb.ReadList(UefiFwBinListBuff, (MeBase+0x10), 4)
	FTPR_Sig = clb.ReadList(UefiFwBinListBuff, (MeBase+0x30), 4)
	if( (FPT_Sig == 0x54504624) and (FTPR_Sig == 0x52505446) ):		# compare with "$FPT" & "FTPR"
		CodePartitionOfst = clb.ReadList(UefiFwBinListBuff, (MeBase+0x38), 4)
		CodePartitionPtr = MeBase + CodePartitionOfst
		CodePartitionSig1 = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr), 4)
		CodePartitionSig2 =clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+0x10), 8)
		if( (CodePartitionSig1 == 0x44504324) and (CodePartitionSig2 == 0x6e616d2e52505446) ):		# compare with "$CPD" & "FTPR.man"
			FTPRmanOfst = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+0x1C), 4)
			ME_Bld_Date = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+FTPRmanOfst+0x14), 4)
			ME_Version = clb.ReadList(UefiFwBinListBuff, (CodePartitionPtr+FTPRmanOfst+0x24), 8)
			MeBldDateStr = "%02X.%02X.%04X" %(((ME_Bld_Date >> 8) & 0xFF), (ME_Bld_Date & 0xFF), ((ME_Bld_Date >> 16) & 0xFFFF))
			MeVerStr = "%d.%d.%d.%d" %((ME_Version & 0xFFFF), ((ME_Version >> 16) & 0xFFFF), ((ME_Version >> 32) & 0xFFFF) , ((ME_Version >> 48)  & 0xFFFF))
			if PrintEn:
				print "ME Version = %s    ME Build Date = %s " %(MeVerStr, MeBldDateStr)
			FwIngrediantDict["ME"]={'Version': MeVerStr, 'Type': '???', 'Date': MeBldDateStr}		# ME Type is tbd

def GetPchStrapsInfo(UefiFwBinListBuff):
	global FwIngrediantDict
	clb.LastErrorSig = 0x0000
	FwIngrediantDict['PCH_STRAPS']={}
	DescBase = 0x00
	FlashValSig = clb.ReadList(UefiFwBinListBuff, (DescBase+0x10), 4)
	if(FlashValSig != 0x0FF0A55A):
		print "Invalid Falsh descriptor section!"
		clb.LastErrorSig = 0x1FD4	# FlashRegionInfo: Invalid Falsh descriptor section
		return 1
	PchStrapsBaseOfst = (clb.ReadList(UefiFwBinListBuff, (DescBase+0x1A), 1) << 4)
	NoOfPchStraps = clb.ReadList(UefiFwBinListBuff, (DescBase+0x1B), 1)
	for StrapNo in range (0, NoOfPchStraps):
		FwIngrediantDict['PCH_STRAPS'][StrapNo] = clb.ReadList(UefiFwBinListBuff, (DescBase+PchStrapsBaseOfst+(StrapNo*4)), 4)

def FetchFwIngrediantInfo(FwBinListBuff, PrintEn=True):
	global FwIngrediantDict
	import XmlCli as cli
	FwIngrediantDict={}
	BiosBase = 0
	BiosLimit = len(FwBinListBuff)
	Status = FlashRegionInfo(FwBinListBuff, PrintEn)
	if(Status == 0):
		GetPchStrapsInfo(FwBinListBuff)
		GetMeInfo(FwBinListBuff, PrintEn)
		cli.FlashAcmInfo(FwBinListBuff, PrintEn)
		BiosBase = FwIngrediantDict['FlashRegions'][BIOS_Region]['BaseAddr']
		BiosLimit = FwIngrediantDict['FlashRegions'][BIOS_Region]['EndAddr']
	cli.ProcessUcode("read", 1, BiosBinListBuff=FwBinListBuff[BiosBase:(BiosLimit+1)], PrintEn=PrintEn)	# Offline mode where we supply the Fw Bin List buffer

