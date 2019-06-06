# -*- coding: utf-8 -*-
###############################################################################
# INTEL CONFIDENTIAL
# Copyright 2008 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.
###############################################################################
# $Id: colorapi.py 225378 2014-08-22 06:40:47Z ashinde $
# $HeadURL: https://ssvn.pdx.intel.com:80/deg/pve/csv/pythonsv/trunk/misc/XmlCli/tools/colorapi.py $
###############################################################################

#######################################################
# Shamelessly ripped off of the many folks before me who
# have done color
#######################################################
import sys,os

######### NEEDED to be able to get attribute info
if sys.platform == "win32":
    from ctypes import windll, Structure, c_short, c_ushort, byref, wintypes

    SHORT = c_short
    WORD = c_ushort

    class COORD(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("X", SHORT),
        ("Y", SHORT)]

    class SMALL_RECT(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("Left", SHORT),
        ("Top", SHORT),
        ("Right", SHORT),
        ("Bottom", SHORT)]

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
      """struct in wincon.h."""
      _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD)]

    # winbase.h
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12

    stdout_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo
    
    # grab default color
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    GetConsoleScreenBufferInfo(wintypes.HANDLE(stdout_handle), byref(csbi))
    _defaultColor = csbi.wAttributes
    if _defaultColor == 0: # fallback..we should never see foreground color default as black
        _defaultColor = 7

colorDictWin = {
        'black'    : 0x0000,
        'blue'     : 0x0001,
        'green'    : 0x0002,
        'cyan'     : 0x0003,
        'red'      : 0x0004,
        'magenta'  : 0x0005,
        'yellow'   : 0x0006,
        'grey'     : 0x0007,
        'white'    : 0x0007,
        'iblack'   : 0x0008,
        'iblue'    : 0x0009,
        'igreen'   : 0x000A,
        'icyan'    : 0x000B,
        'ired'     : 0x000C,
        'imagenta' : 0x000D,
        'iyellow'  : 0x000E,
        'igrey'    : 0x000F,
        'iwhite'   : 0x000F,
        }

# SVOS format:  "\"\e[1;34m\"",
colorDictSvos = {
        'black'   : (0,30),
        'blue'    : (0,34),
        'green'   : (0,32),
        'cyan'    : (0,36),
        'red'     : (0,31),
        'magenta' : (0,35), # purple
        'yellow'  : (0,33),
        'grey'    : (0,38),
        'white'   : (0,37),
        'iblack'  : (1,30),
        'iblue'   : (1,34),
        'igreen'  : (1,32),
        'icyan'   : (1,36),
        'ired'    : (1,31),
        'imagenta': (1,35),
        'iyellow' : (1,33),
        'igrey'   : (1,37),
        'iwhite'  : (1,37),
        }

import sys

def isColorValid(colorname):
    if sys.platform == "win32":
        if not colorDictWin.has_key(colorname):
            raise ValueError("Unknown color: %s"%colorname)
    else:
        if not colorDictSvos.has_key(colorname):
            raise ValueError("Unknown color: %s"%colorname)

def resetColor():
    """set console back to black background, white foreground"""
    if sys.platform == "win32":
        SetConsoleTextAttribute(stdout_handle, _defaultColor)
    else: # assume its linux
        fg_p1,fg_p2 = colorDictSvos['iwhite'] 
        bg_p1,bg_p2 = colorDictSvos['black']
        sys.stdout.write("\033[%s;%sm"%(fg_p1,fg_p2))
        sys.stdout.write("\033[%s;%sm"%(bg_p1,bg_p2+10))

def setFgColor(color):
    """set console foreground color"""
    if sys.platform == "win32":
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        GetConsoleScreenBufferInfo(stdout_handle, byref(csbi))
        oldcolor = csbi.wAttributes
        oldcolor &= ~(0x0F)        
        SetConsoleTextAttribute(stdout_handle, oldcolor|colorDictWin[color])
    else: # assume its linux
        p1,p2=colorDictSvos[color]
        #os.system("echo -e \"\e[%s;%sm\""%(p1,p2))
        sys.stdout.write("\033[%s;%sm"%(p1,p2))
        #os.system("echo -e \"\e[%s;%sm\""%(p1,p2))

def setBgColor(color):
    """set console background color"""
    if sys.platform == "win32":
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        GetConsoleScreenBufferInfo(stdout_handle, byref(csbi))
        oldcolor = csbi.wAttributes
        oldcolor &= ~(0xF0)
        SetConsoleTextAttribute(stdout_handle, oldcolor|(colorDictWin[color]<<4))
    else: # assume its linux
        p1,p2=colorDictSvos[color]
        sys.stdout.write("\033[%s;%sm"%(p1,p2+10))

def setColor(fgcolor,bgcolor):
    """Used to set both foreground and background color at once"""
    if sys.platform == "win32":
        fgnum = colorDictWin[fgcolor]
        bgnum = colorDictWin[bgcolor]
        SetConsoleTextAttribute(stdout_handle, fgnum|(bgnum<<4))
    else: # must be linux
        fg_p1,fg_p2 = colorDictSvos[fgcolor]
        bg_p1,bg_p2 = colorDictSvos[bgcolor]
        sys.stdout.write("\033[%s;%s;%sm"%(fg_p1,fg_p2,bg_p2+10))

