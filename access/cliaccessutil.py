#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Cscripts remove start
################################################################################
# INTEL CONFIDENTIAL
# Copyright 2005 2006 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to the
# source code ("Material") are owned by Intel Corporation or its suppliers or
# licensors. Title to the Material remains with Intel Corporation or its sup-
# pliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and lic-
# ensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing
#################################################################################
# Cscripts remove end

class cliaccess(object):
	def __init__(self,accessname):
		self.__dict__["InterfaceType"] = accessname

	def __setattr__(self, attribute, value):
		if not attribute in self.__dict__:
			print "Cannot set %s" % attribute
		else:
			self.__dict__[attribute] = value

	def haltcpu(self, delay):
		assert False, "cliaccess is a virtual class!"

	def runcpu(self):
		assert False, "cliaccess is a virtual class!"

	def InitInterface(self):
		assert False, "cliaccess is a virtual class!"

	def CloseInterface(self):
		assert False, "cliaccess is a virtual class!"

	def warmreset(self):
		assert False, "cliaccess is a virtual class!"

	def coldreset(self):
		assert False, "cliaccess is a virtual class!"

	def memBlock(self, address, size):
		assert False, "cliaccess is a virtual class!"

	def memsave(self, filename, address, size):
		assert False, "cliaccess is a virtual class!"

	def memread(self, address, size):
		assert False, "cliaccess is a virtual class!"

	def memwrite(self, address, size, value):
		assert False, "cliaccess is a virtual class!"

	def load_data(self, filename, address):
		assert False, "cliaccess is a virtual class!"

	def readIO(self, address, size):
		assert False, "cliaccess is a virtual class!"

	# Write IO function
	def writeIO(self, address, size, value):
		assert False, "cliaccess is a virtual class!"

	# Trigger S/W SMI of desired value
	def triggerSMI(self, SmiVal):
		assert False, "cliaccess is a virtual class!"

	def ReadMSR(self, Ap, MSR_Addr):
		assert False, "cliaccess is a virtual class!"

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		assert False, "cliaccess is a virtual class!"

	def ReadSmbase(self):
		assert False, "cliaccess is a virtual class!"
