#!/usr/bin/env python
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
# $Id: toolbox.py 225378 2014-08-22 06:40:47Z ashinde $
# $HeadURL: https://ssvn.pdx.intel.com:80/deg/pve/csv/pythonsv/trunk/misc/XmlCli/tools/toolbox.py $
###############################################################################
"""
Once the toolbox has been imported, you can create your own logger for your script. All 
messages will still be sent to the root logger once your logger is done with them. 
This allows for your script to write to its own log file, while the root logger still 
records the information in the 'root' logfile (currently this is 'pythonsv.log'). 

The follow is example syntax on how to get a logger::

    import common.toolbox
    # this will return the script's logger:
    _log = common.toolbox.getLogger('mylogger') 
    # this will set the log file (this is optional)
    _log.setFile("mylogfile.log")

    def somefunction():
       global _log
       # by default this goes to the screen and file:
       _log.result("This is a message with a result") 
       # by default this goes only to the file:
       _log.info("This is a message with INFO") 
       # by default this goes ...  nowhere. The log level must be set lower to see this message
       _log.debug("This is a message with DEBUG")

The follow functions exist to customize your logger's behaviour:

.. automethod:: EasyLogger.setFile
.. automethod:: EasyLogger.closeFile

Log Levels
------------

You can control the 'level' at which something goes to the file or screen. The level can be
passed in as a string (if it is a predefined level) or a number (for ultimate customization). Here
is a list of the predefined levels.

All of the predefined levels have a corresponding logger function so that you can use the format of:: 

    mylog.level(message) 

instead of::

    mylog.log(level,message)

=============   ==========      =============  
Level String    Level Num       Example Call
=============   ==========      =============  
CRITICAL        50              logger.critical("some mesage")
ERROR           40              logger.error("some mesage")
WARNING         30              logger.warning("some mesage")
RESULT          25              logger.result("some mesage")
INFO            20              logger.info("some mesage")
DEBUG           10              logger.debug("some mesage")
DEBUGALL        5               logger.debugall("some mesage")
=============   ==========      =============  


Here are the functions for setting the level:

.. automethod:: EasyLogger.setFileLevel
.. automethod:: EasyLogger.getFileLevel
.. automethod:: EasyLogger.setConsoleLevel
.. automethod:: EasyLogger.getConsoleLevel
.. automethod:: EasyLogger.getMinLevel
.. automethod:: EasyLogger.getMaxLevel


Log Formats
------------

The logging module supports a whole ton of formatting options. To help 
simplify things, the setConsoleFormat and setFileFormat take a string 
or a format object. For the string, you can specifiy one of these default formats:

============    ===================
Name            Format's Output in a log file
============    ===================
simple          message (default for the console output)
level           level : message
time            time : level : message
debug           time : module : lineno : level : message (default for the fileoutput)
============    ===================

Or you can specify create your own format object by using the logging module and pass it 
in as parameter instead. See the python logging module for documentation on format objects. 

.. don't automethod these since the help in the file rehashes the possible levels

.. method:: EasyLogger.setFileFormat(format)
.. method:: EasyLogger.setConsoleFormat(format)

Using Color
------------
Any of the logger calls can also be used to output in color to the screen.
Any special color characters will be removed before they are sent to the log
files. Also the way the color is handled is platform independant so the code
does not have to know about linux vs. windows.

The color is handled by passing a special delimiter around the color to display. An example::

    mylog.result("\\001ired\\001Testing the color red and \\001blue\\001.")
  
The out put will look like this:

.. font:: color=red Testing the color red 

    .. |Testing the color red| font:: color=red
  
 

"""
import sys,string,os
import logging,types
import logging.handlers
import colorapi

####
#### This is to help with scripts using older apply_param syntax
####

_color_delim = "\001"
_debug = False



################################################################
############ LOGGING ##########################################
################################################################
DEBUGALL = logging.DEBUGALL = 1
DEBUG    = logging.DEBUG
ACCESS   = logging.ACCESS  = 19   
INFO     = logging.INFO
RESULT   = logging.RESULT = 25
WARNING  = logging.WARNING
ERROR    = logging.ERROR
CRITICAL = logging.CRITICAL
_levelnames = {\
    'DEBUGALL':DEBUGALL,
    'DEBUG'   :DEBUG,
    'ACCESS'  :ACCESS,
    'INFO'    :INFO,
    'RESULT'  :RESULT,
    'WARNING' :WARNING,
    'ERROR'   :ERROR,
    'CRITICAL':CRITICAL}

logging.addLevelName(RESULT,"RESULT")

if sys.version_info[0] >= 2 and sys.version_info[1] >= 4:
    _originalLogger = logging.getLoggerClass()
else:
    _originalLogger = logging._loggerClass
_originalRoot = logging.RootLogger

#######
# This Code needed for additional result/debugall functions
# it is cut & paste from the logging module
#######
#
# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#
if hasattr(sys, 'frozen'): #support for py2exe
    _srcfile = "logging%s__init__%s" % (os.sep, __file__[-4:])
elif string.lower(__file__[-4:]) in ['.pyc', '.pyo']:
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
# now make path and case consistent
_srcfile = os.path.normpath(_srcfile)
_srcfile = os.path.normcase(_srcfile)


class EasyLogger(_originalLogger):

    def __init__(self,name,stream=sys.stdout):
        """
        :param newline: Specifies whether to add on a newline character or not
                        when sending to the console or logfile
        """
        # first call the default handler
        _originalLogger.__init__(self,name)
        if _debug: print "Logger created: %s"%name
        # now on to our custom stuff
        self._logfile = None
        self._fileHandler = None
        self._consoleHandler = None
        self._newline = True # default to always specifying newline
        self._filter  = True # used for controlling whether we pass up log messages to "parents"
        self._dynamic = False
        self._dynamicLevel = INFO
        self._dynamicFormat = "debug"
        self._dynamicOptions = {} # save off options for setFile
        # this prevents each type of set function from working
        # so that the logger can be "locked" at the command prompt
        self.lockedFileName = False
        self.lockedFileLevel = False
        self.lockedFileFormat = False
        self.lockedConLevel = False
        self.lockedConFormat = False

        # Create a stream handler that will only print a
        # message once
        if name != "root":
            # if not root, print simple and default is result
            self._consoleHandler = StreamOnceHandler(stream,newline=self._newline)
            self.addHandler(self._consoleHandler)
            self.setConsoleFormat("simple")
            self.setConsoleLevel(RESULT)
        else:
            # root should be off by default, but use debug when turned on
            self._consoleHandler = StreamOnceHandler(stream,newline=self._newline)
            self.addHandler(self._consoleHandler)
            self.setConsoleFormat("simple")
            self.setConsoleLevel(60) # turns off display

        # if using python 2.5 or newer, then we can "fix" find caller
        if sys.version_info[0] >= 2 and sys.version_info[1] >= 5:
            EasyLogger.findCaller = self.findCaller_25

    def setNewline(self,newline):
        """
        :param newline: True/False - specifies whether to append a newline character or now
        """
        self._newline = newline
        for handler in self.handlers:
            handler.newline = newline

    def getNewline(self):
        """Returns True/False on whether this function automatically inserts the newline"""
        return self._newline

    def findCaller_25(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        # this only works on 2.5 (it should work on 2.4, but the SVOS
        # version must have an odd 2.4)
        # This had to be modified from logging to make the logfile
        # line # info stay accurate
        f = sys._getframe().f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normpath(co.co_filename)
            filename = os.path.normcase(filename)
            loggingsrcfile = os.path.normpath(logging._srcfile)
            loggingsrcfile = os.path.normcase(loggingsrcfile)
            if filename == _srcfile or filename == loggingsrcfile:
                f = f.f_back
                continue
            rv = (filename, f.f_lineno, co.co_name)
            break
        return rv

    def result(self,msg,*args,**kwargs):
        self.log(RESULT,msg,*args,**kwargs)

    def debugall(self,msg,*args,**kwargs):
        self.log(DEBUGALL,msg,*args,**kwargs)
        
    def access (self,msg,*args,**kwargs):
        self.log(ACCESS,msg,*args,**kwargs)

    def closeFile(self):
        """use this to close any open files before moving the log file you have created"""
        self.setFile(None)
        
    def setFile(self,filename,maxMegaBytes=50,backupCount=3,overwrite=False,dynamic=False,newline=True,binary=False):
        """
        Specifies name of logfile to use, if not called, then no logfile 
        will be used.

        If called twice, then the old logfile will no longer be used. 
        This makes it 'safe' to reload scripts that call this function

        if filename==None, then it will close the logfile and
        remove the logHandler for this file

        :param filename:      path of file to log to
        :param maxMegaBytes:  # of megabytes before doing "rollover" and
                              starting a new file
        :param backupCount:   max # of files to keep before deleteing old ones
        :param overwrite:     overwrite the old log file if it exists
        :param dynamic:       if True, then only open log file if the level (specified by setFileLevel) is used
        :param binary:        whether to open in binary mode (controls how line endings are handled)
        """
        if self.lockedFileName:
            self.log(logging.WARNING,"Not changing logfile to '%s' b/c this logger is locked"%filename)
            # if filename has been locked, do nothing
            return

        # if fileHanlder is currently open, close it properly
        if self._fileHandler!=None:
            # need to do this to remove from know logging's known handlers
            self._fileHandler.close() 
            self.removeHandler(self._fileHandler)
            self._fileHandler = None
        if filename==None:
            # if filename is None, then this was called just to close
            # the previous file properly, so we're done
            return
        # save off current logfile name/path
        self._filename=filename
        self._dynamic=dynamic

        if dynamic:
            # if dynamic, save off our calling options and quitea
            self._dynamicOptions={'filename':filename,
                                  'maxMegaBytes':maxMegaBytes,
                                  'backupCount':backupCount,
                                  'overwrite':overwrite,
                                  'dynamic':False, # when we enable log file, we turn dynamic off
                                  }
            return

        oldformat = None
        if overwrite == True:
            filemode = "w"
            maxMegaBytes=0
        else:
            filemode = "a"

        if binary:
            filemode += "b"

        try:
            newhandler = RotateWithControl(filename,filemode,
                                (maxMegaBytes*1024*1024),backupCount,newline=self._newline)
        except Exception, e:
            print "ERROR: could not open logfile: %s"%filename
            import traceback
            traceback.print_exc()
            return

        # now add our new handler
        self.addHandler(newhandler)
        # now save off the file handler for later reference
        self._fileHandler = newhandler
        # by default set format to debug
        self.setFileFormat("debug")
        self.setFileLevel("INFO")

    def _log(self,level,msg,*args,**kwargs):
        if self._dynamic and level>=self._dynamicLevel:
            # then turn on log file
            self.setFile(**self._dynamicOptions)
            self.setFileLevel(self._dynamicLevel)
            self.setFileFormat(self._dynamicFormat)
        _originalLogger._log(self,level,msg,*args,**kwargs)

    def setFiltering(self,enable):
        """
        Use to specify whether this logger filter's messages from its parents
        only disable this if you are using nested logging
        enable=True  - log messages are ignore if they aren't used by our console/file handler.
                       parent logger's will still get these messages, but only if we use them also
        enable=False - all log messages are processed by this logger, then given to parent logger
        """
        self._filter = enable
        if not self._filter:
            self.level = 1
        else:
            self.level = self.getMinLevel()

    def setFileLevel(self,level):
        """
        Set the level for determining when messages are sent the file

        :param level:  number or string representing min level before something 
                       gets logged to a file
        """
        if _debug: "Changing File %s to %s"%(self.name,level)
        if self.lockedFileLevel:
            self.log(logging.WARNING,"Not changing file level to '%s' b/c this logger is locked"%str(level))
            # if filename has been locked, do nothing
            return

        # make sure levelname is number we need
        if type(level) == type(""): # if level is a string, decode it
            level = level.upper()
            if level not in _levelnames.keys():
                raise ValueError("Invalid level name: %s"%level)
            level = _levelnames[level]

        # otherwise assume level is an int, and leave it
        # if dynamic is on then file should still be closed, so just set level
        if self._dynamic:
            self._dynamicLevel = level
            # make sure we don't filter out these messages
            if self.level > level:
                self.level = level
            return

        if self._fileHandler==None:
            raise AssertionError("No Local File Handler has been set")
        self._fileHandler.setLevel(level)
        
        # make sure our logger puts whatever the new level is to the file 
        if self._filter:
            self.level = self.getMinLevel()

    def getFileLevel(self):
        """Get the level at which we send messages to the file"""
        if self._fileHandler==None:
            # if no file handle, then just return max
            return 99
        level = self._fileHandler.level
        # if we can't find the level name then just return the number
        if level not in logging._levelNames.keys():
            return level
        else:
            return logging._levelNames[level]

    def getMaxLevel(self):
        """used to get the max level between Console and File Level """
        if self._consoleHandler==None: clevel = None
        else:                          clevel = self._consoleHandler.level
        if self._fileHandler==None:    flevel = None
        else:                          flevel = self._fileHandler.level
        # we're going to return minimum level between console and file
        maxlevel = max(flevel,clevel)
        return maxlevel

    def getMaxLevelName(self):
        maxlevel = self.getMaxLevel()
        if maxlevel not in logging._levelNames.keys():
            return maxlevel
        else:
            return logging._levelNames[maxlevel]

    def getMinLevel(self):
        """used to get the lowest level between Console and File Level """
        if self._consoleHandler==None: clevel = 99
        else:                          clevel = self._consoleHandler.level
        if self._fileHandler==None:    flevel = 99
        else:                          flevel = self._fileHandler.level
        # we're going to return minimum level between console and file
        minlevel = min(flevel,clevel)
        return minlevel

    def getMinLevelName(self):
        """Try to return min level as string"""
        minlevel = self.getMinLevel()
        if minlevel not in logging._levelNames.keys():
            return minlevel
        else:
            return logging._levelNames[minlevel]


    def getConsoleLevel(self):
        """Get the level at which we send messages to the console"""
        if self._consoleHandler==None:
            # if no file handle, then just return max
            return 99
        level = self._consoleHandler.level
        # if we can't find the level name then just return the number
        if level not in logging._levelNames.keys():
            return level
        else:
            return logging._levelNames[level]

    def setConsoleLevel(self,level):
        """
        Set the level for determining when messages are sent to the Console

        :param level:  number or string representing min level before something 
                       gets logged to a file
        """
        if _debug: print "Changing Console %s to %s"%(self.name,level)
        if self.lockedConLevel:
            self.log(logging.WARNING,"Not changing console level to '%s' b/c this logger is locked"%str(level))
            # if filename has been locked, do nothing
            return
        if self._consoleHandler==None:
            raise AssertionError("No Local File Handler has been set")
        if type(level) == type(""): # if level is a string, decode it
            level = level.upper()
            if level not in _levelnames.keys():
                raise ValueError("Invalid level name: %s"%level)
            self._consoleHandler.setLevel(_levelnames[level])
        else: # otherwise, assume its an int
            self._consoleHandler.setLevel(level)

        # only decrease our overall level if filtering is on
        if self._filter:
            self.level = self.getMinLevel()


    def _setFormat(self,format,handler):
        """Use this to give a standard name/behavior
        between the console and the file handler
        """
        # othwerwise, create the one that was specified
        if format=="simple":
            formatstr = "%(message)s"
        elif format == "level":
            formatstr = "%(levelname)-9s:%(message)s"
        elif format == "time":
            formatstr = "%(asctime)s:%(levelname)-9s:%(message)s"
        elif format=="debug":
            formatstr = "%(asctime)s:%(module)-12s:%(lineno)-3s:%(levelname)-9s:%(message)s"
        else:
            raise ValueError("Unexpected format Value: %s"%format)

        # create the new formatter
        formatstr = logging.Formatter(formatstr,"%m-%d %H:%M")
        # now set the file handler to use it
        handler.setFormatter(formatstr)

    def setConsoleFormat(self,format):
        """
        Specifies the format used when sending the message to the file
        You can either use one of the predefine names, or pass in a
        format object (see python help on logging.Formater Objects)

        :param format: format to use for console output

        simple -  message
        level  -  level : message
        time   -  time : level : message
        debug  -  time : module : lineno : level : message


        """
        if self.lockedConFormat:
            self.log(logging.WARNING,"Not changing console formate to '%s' b/c this logger is locked"%str(format))
            # if filename has been locked, do nothing
            return

        if self._consoleHandler==None:
            raise AssertionError("No Local File Handler has been set")

        if format.__class__ ==logging.Formatter:
            # if this is a formatter, then just use it
            self._consoleHandler.setFormatter(format)
        else:
            self._setFormat(format,self._consoleHandler)

    def setFileFormat(self,format):
        """
        Specifies the format used when sending the message to the file
        You can either use one of the predefine names, or pass in a
        format object (see python help on logging.Formater Objects)

        :param format: format to use for console output

        simple -  message
        level  -  level : message
        time   -  time : level : message
        debug  -  time : module : lineno : level : message

        Time format is month-day hour:minute
        """
        if self.lockedFileFormat:
            self.log(logging.WARNING,"Not changing file formate to '%s' b/c this logger is locked"%str(format))
            # if filename has been locked, do nothing
            return

        if self._dynamic:
            self._dynamicFormat = format
            return

        if self._fileHandler==None:
            raise AssertionError("No Local File Handler has been set")

        if format.__class__==logging.Formatter:
            # if this is a formatter, then just use it
            self._fileHandler.setFormatter(format)
            return
        else:
            self._setFormat(format,self._fileHandler)
            
    def flush(self):
        """make sure all file handlers have flushed to disk, and stream handlers have been flushed also"""
        for h in self.handlers:
            h.flush()
            if hasattr(h.stream,"fileno"):
                os.fsync(h.stream.fileno())

    def lockFilename(self):
        """Prevents log file from changing"""
        self.lockedFileName = True

    def lockFileLevel(self):
        """Prevents file's log level from changing"""
        self.lockedFileLevel = True

    def lockFileFormat(self):
        """Prevents file's log format from changing"""
        self.lockedFileFormat = True

    def lockConsoleLevel(self):
        """Prevents console's log level from changing"""
        self.lockedConLevel = True

    def lockConsoleFormat(self):
        """Prevents console's log format from changing"""
        self.lockedConFormat = True



_previousRecord = None
class StreamOnceHandler(logging.StreamHandler):
    def __init__(self,*args,**kwargs):
        if kwargs.has_key('newline'):
            self.newline = kwargs.pop('newline')
        else:
            self.newline = True # default is true...
        return logging.StreamHandler.__init__(self,*args,**kwargs)

    def emit_orig(self,msg):
        try:
            fs = "%s"
            if not hasattr(types, "UnicodeType"): #if no unicode support...
                self.stream.write(fs % msg)
            else:
                try:
                    self.stream.write(fs % msg)
                except UnicodeError:
                    self.stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(msg)

    def emit(self,record):
        colorused = False
        try:
            msg = self.format(record) 
            if msg.find("\001")==-1: # big speedup for when no color is present
                self.emit_orig(msg)
            else: # must have some color                
                msglist = msg.split(_color_delim)
                if len(msglist)>1:
                    colorused=True
                for t,text in enumerate(msglist):
                    if t%2==0: # regular text:
                        self.emit_orig(text)
                    else: # must be color
                        colorlist = text.split(",")
                        # first color is foreground
                        if len(colorlist)==1:
                            color = colorlist[0].strip()
                            if color=='reset':
                                colorapi.resetColor()
                            else:
                                colorapi.setFgColor(color) # make sure any excess whitespace is removed
                        # if both given, then second color is background
                        elif len(colorlist)==2:
                            colorapi.setColor(colorlist[0].strip(),colorlist[1].strip()) # make sure any excess whitespace is removed                                               
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
        # put it back if we touched the color
        if colorused:
            colorapi.resetColor()

        # send out a newline if that was requested...
        # do this after we have reset the color...
        if self.newline:
            self.emit_orig("\n")

    def handle(self,record):
        global _previousRecord
        if record == _previousRecord:
            # don't bother handling, if its the
            # same as the previous record
            return
        _previousRecord = record
        return logging.StreamHandler.handle(self,record)

def removeChart(text):
    """
    Removes characters some table characters from text that dont show up in the log file correctly
    """
    # translate works by looking up ord(text[c]) in this long string to see what what the character should be converted to
    if isinstance(text, types.StringType):
        return text.translate('\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2||||-=||==-=----|-+||====|===-=--==-+|--\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff')
    # not a standard string...punt
    return text

def removeColor(text):
    """Function for removing any color delimiter and information from a string of text"""
    # remove any color
    text = text.split(_color_delim)
    text = ''.join( [text[x] for x in range(len(text)) if(x%2)==0])
    return text

class RotateWithControl(logging.handlers.RotatingFileHandler):
    def __init__(self,*args,**kwargs):
        if kwargs.has_key('newline'):
            self.newline = kwargs.pop('newline')
        else:
            self.newline = False
        # now call our parent
        logging.handlers.RotatingFileHandler.__init__(self,*args,**kwargs)

    def ll_emit(self,record):
        """this is similar to the low level emit code that
        is in stream handler, but it has a conditional for the newline
        """
        try:
            msg = self.format(record)
            if self.newline:
                msg += "\n"
            msg = removeColor(msg)
            msg = removeChart(msg)

            if not hasattr(types, "UnicodeType"): #if no unicode support...
                self.stream.write(msg)
            else:
                try:
                    self.stream.write(msg)
                except UnicodeError:
                    self.stream.write(msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def emit(self,record):
        """
        taken from RolloverBase, but calls our emit instead of
        the base level emit
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            self.ll_emit(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

#######################################
# This is the initialization code for overriding
# the root logger and installing our new logger class
#######################################
def loggingInit():
    global getLogger

    # if init has been run OR easy logger is somehow already present
    # AKA atlas logger and pythonsv logger both present
    if hasattr(logging,"EasyLogger") and logging.EasyLogger==True:
        return

    # record that we have done init so that it doesnt get done again
    logging.EasyLogger = True

    logClass = logging.getLoggerClass()

    # let others have access
    logging.StreamOnceHandler = StreamOnceHandler
    # Future logging instances should come from
    # this logger
    logging.setLoggerClass(EasyLogger)
    logging.RootLogger = EasyLogger
    # we must override the root logger in order to get
    # the new functions
    # create our new root logger
    logging.root = logging.getLogger('root')
    EasyLogger.manager.root = logging.root


loggingInit()

def getLogger(name=None,**kwargs):
    """
    get the logger and if 'newline=False' is passed in
    the set that logger to not automatically do newlines
    :param newline: optional parameter that can be set to false to
                    prevent logger from adding a newline
    """
    if name in [None,""]: # dont give out the root logge by default
        name = "default" 
    logobj = logging.getLogger(name)
    # default is whatever we had in the past
    newline = kwargs.get('newline',logobj._newline)
    logobj.setNewline(newline)
    return logobj

def print_msg(msg,level):
    """This is only for legacy purposes, I recommend calling
    logging.getLogger and using the functions that come with
    that instead
    """
    dflt = logging.getLogger('default')
    dflt.log(level,msg)

##########################
###
### Only coded here for the apply params to work
###
##########################
_logname = "root"
def _setLogName(name):
    global _logname
    _logname=name

def _setConsoleLevel(*param):
    global _logname
    if len(param)==2:
        logname =param[0]
        loglevel=param[1]
    elif len(param) == 1:
        logname = _logname
        loglevel=param[0]
    else:
        raise Exception("valid arguments are 'logname level' or just 'level'")

    logger = logging.getLogger(logname)
    logger.setConsoleLevel(loglevel)
    logger.lockConsoleLevel()

def _setFileLevel(*param):
    global _logname
    if len(param)==2:
        logname =param[0]
        loglevel=param[1]
    elif len(param)==1:
        logname = _logname
        loglevel=param[0]
    else:
        raise Exception("valid arguments are 'logname level' or just 'level'")

    logger = logging.getLogger(logname)
    logger.setFileLevel(loglevel)
    logger.lockFileLevel()

def _setFileFormat(*param):
    global _logname
    if len(param)==2:
        logname =param[0]
        format=param[1]
    elif len(param)==1:
        logname = _logname
        format=param[0]
    else:
        raise Exception("valid arguments are 'logname format' or just 'format'")

    logger = logging.getLogger(_logname)
    logger.setFileFormat(format)
    logger.lockFileFormat()

def _setConsoleFormat(*param):
    global _logname
    if len(param)==2:
        logname =param[0]
        format=param[1]
    elif len(param)==1:
        logname = _logname
        format=param[0]
    else:
        raise Exception("valid arguments are 'logname format' or just 'format'")

    logger = logging.getLogger(logname)
    logger.setConsoleFormat(format)
    logger.lockConsoleFormat()

def _setFile(*param):
    global _logname
    logname = _logname

    if "w" == param[-1] or "wr" == param[-1]:
        overwrite    = True
        maxMegaBytes = 0
    else:
        overwrite    = False
        maxMegaBytes = 50

    if len(param) == 3 and (param[-1]=="w" or param[-1]=="wr"):
        logname =param[0]
        filename=param[1]
    elif len(param) == 2 and (param[-1]=="w" or param[-1]=="wr"):
        filename=param[0]
    elif len(param) == 2: # no write specified
        logname =param[0]
        filename=param[1]
    elif len(param) == 1:
        filename=param[0]
    else:
        errmsg = "valid argments are:\n"
        errmsg += "\tlogger filename w\n"
        errmsg += "\tlogger filename\n"
        errmsg += "\tfilename w\n"
        errmsg += "\tfilename\n"
        raise Exception(errmsg)

    logger = logging.getLogger(logname)
    logger.setFile(filename,maxMegaBytes,3,overwrite)
    logger.lockFilename()

def showbits(value, num_bits=-1):
    """Takes any integer value and displays in MSb first, binary format with
    the individual bits labeled. If num_bits is specified to a positive
    integer, the display will show up to num_bits-1 position. Else the
    it will show up to the highest set bit found in the value."""    
    try:
        ivalue = long(value)
    except ValueError, e:    
        raise TypeError("value %s (type %s) cannot be interpreted as an integer!" % (repr(value), type(value)))
        
    if ivalue <= 0:    
        raise ValueError("value %s is not positive, non-zero integer!" % repr(value))
    
    if num_bits > 0:
        high_bit = num_bits
    else:
        high_bit = 0
        tmp = ivalue
        while tmp != 0:
            tmp = tmp >> 1
            high_bit += 1

    #sys.stdout.write('msb-> \n') # is this necessary?
    
    sys.stdout.write('  b | ')
    if high_bit >= 100:
        for n in reversed(range(0,high_bit)):
            if n > high_bit: continue
            sys.stdout.write(str(n/100))
    sys.stdout.write('\n')
    
    sys.stdout.write('  i | ')
    if high_bit >= 10:
        for n in reversed(range(0,high_bit)):
            if n > high_bit: continue
            sys.stdout.write(str((n/10)%10))
    sys.stdout.write('\n')
        
    sys.stdout.write('  t v ')
    for n in reversed(range(0,high_bit)):
        if n > high_bit: continue
        sys.stdout.write(str(n%10))
    sys.stdout.write('\n')    
    
    sys.stdout.write('------' + ('-' * high_bit) + '\n')
        
    sys.stdout.write('val-> ')
    for n in reversed(range(0,high_bit)):
        sys.stdout.write(str((ivalue >> n) & 1))
    sys.stdout.write('\n')

def showallcolors():
    """
    This function displays all the color combos that are possible in the 
    logging module. The text in the box is foreground/background
    """
    mylog = getLogger('toolbox_test')
    mylog.setNewline(False)
    colors = colorapi.colorDictWin.keys() # shouldn't matter about win vs. svos since they are the same
    colors.sort()
    i = 0 # every 5 colors we'll start a newline
    for c1 in colors:
        for c2 in colors:
            mylog.result("\001%s,%s\001%8s/%-8s"%(c1,c2,c1,c2))
            i += 1
            if i%4==0:
                mylog.result("\n")
    pass

def testlogger():
    mylog = getLogger('toolbox_test')
    #mylog.setNewline(False)
    mylog.setFile("toolbox_test.nonewline.txt")
    mylog.setFileFormat('simple')
    mylog.info("Blah")
    mylog.result("\001ired\001...yo testing..")
    mylog.result("\001blue,igreen\001Crazy colors")
    mylog.result("\001blue,iwhite\001Crazy colors")
    mylog.result("\001magenta\001Magenta")
    mylog.result("Testing it in the \001ired\001middle\001iwhite\001 of the string")
    mylog.result("Testing a bogus delimiter in the line \001without any color")
    mylog.result("Blah2")

if __name__=="__main__":
    #testlogger()
    showallcolors()
    

