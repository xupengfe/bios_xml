############################################################################
# INTEL CONFIDENTIAL
# Copyright 2006 2007 Intel Corporation All Rights Reserved.
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
pysvtype = None
try:
	import components.corecode as _core
	pysvtype = "components"
except:
	import namednodes.utils.wrappedvalue as _nnwrappedvalue
	pysvtype = "namednodes"

def int2mask(val,length=1):
	assert isNumber(val),"Cannot call int2mask with nonNumber type. type(val)=%s"%type(val)
	val_bitmask=[]
	while 2**len(val_bitmask) <= val:
		val_bitmask.append((val >> len(val_bitmask)) & 1)
	if len(val_bitmask) < length:
		val_bitmask.extend([0]*(length-len(val_bitmask)))
	return val_bitmask
	
def mask2int(bitarray):
	ret=0
	for b in range(len(bitarray)):
		ret+=(bitarray[b]*(2**b))
	return ret


def isNumber(val):
	if pysvtype == "components":
		return isinstance(val, (_types.LongType,_types.IntType,_types.FloatType,_core.UserLong))
	elif pysvtype == "namednodes":
		return isinstance(val, (_types.LongType,_types.IntType,_types.FloatType,_nnwrappedvalue.WrappedValue))
	else:
		assert False, "Unknown pysvtype. Expecting components or namednodes"
	
def isString(val):
	return isinstance(val, (_types.StringType,_types.UnicodeType))

def str2long(input_val, default_base=16):
	# convert from the source base to the target base; work in decimal in between
	if isNumber(input_val):
		return input_val
	elif isinstance(input_val,(_types.StringType,_types.UnicodeType)):
		base=default_base
		if input_val.lower().startswith("0x"):
			base=16
			input_val=input_val[2:]
		elif input_val.lower().startswith("0n"):
			base=8
			input_val=input_val[2:]
		elif input_val.lower().startswith("0y"):
			base=2
			input_val=input_val[2:]
		
		return long(input_val,base)
	else:
		raise TypeError,"Function _str2long doesn't know how to handle input of type %s"%type(input_val)