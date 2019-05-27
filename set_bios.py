#!/usr/bin/python2.7

import os

FOLDER_PATH = '/root/bios_xml'
LINUX_VER = os.popen('uname -r').read()
LINUX_VER = LINUX_VER.rstrip()
DATE = os.popen('date +%y-%m-%d_%H_%M').read()
DATE = DATE.rstrip()
DDT_LOG = '/opt/logs/ddt_' + LINUX_VER + '_' + DATE
DDT_PATH = os.popen('ls -1 /home/* | grep ^/home | grep "ltp-ddt_" | tail -n 1 | cut -d ":" -f 1').read()
DDT_PATH = DDT_PATH.rstrip()

def usage():
    print "python2.7 set_bios.py platform_rvp FUNC"
    print "platform_rvp: example cfl-h-rvp | whl-u-rvp | cml-u-rvp | aml-y-rvp | icl-u-rvp"
    print "FUNC: optional example none|user|secure|dp or rerun | clear"
    os._exit(2)

def set_bios_none():
    import sys
    sys.path.append(r"/root/bios_xml/")
    import XmlCli as cli
    cli.clb._setCliAccess("linux")
    cli.clb.ConfXmlCli()
    cli.CvProgKnobs("EnableSgx=0x01, PrmrrSize=0x08000000, EnableAbove4GBMmio=0x01, PrimaryDisplay=0x00, PrimaryDisplay_inst_2=0x00, PrimaryDisplay_inst_3=0x00, PcieSwEqOverride=0x01, PcieRootPortAspm_20=0x02, PcieRootPortDptp_20=0x05, PcieRootPortHPE_20=0x01, Rtd3Tbt=0x01, DiscreteTbtSupport=0x01, TbtVtdBaseSecurity=0x01, TbtBootOn=0x02, TrOsup=0x01")
    cli.CvProgKnobs("SecurityMode=0x00, TBTHotSMI=0x00, TBTHotNotify=0x00, Gpio5Filter=0x00, TBTSetClkReq=0x01, TbtLtr=0x01, TbtL1SubStates=0x00, Win10Support=0x02, DTbtController_0=0x01, DTbthostRouterPortNumber_0=0x02, DTbtPcieExtraBusRsvd_0=0x6A, DTbtPcieMemRsvd_0=0x02E1, DTbtPciePMemRsvd_0=0x04A0, CsmControl=0x01, BootOrder_3=0x0003, BootOrder_4=0x0002, BootOrder_5=0x0000, AfterEoP=0x00")
    echo_none = 'echo none_set_done > /root/bios_xml/next_step'
    os.system(echo_none)
    print 'set none_set_done into /root/bios_xml/next_step'
    #os.system('reboot')

def set_bios_user():
    import sys
    sys.path.append(r"/root/bios_xml/")
    import XmlCli as cli
    cli.clb._setCliAccess("linux")
    cli.clb.ConfXmlCli()
    cli.CvProgKnobs("EnableSgx=0x01, PrmrrSize=0x08000000, EnableAbove4GBMmio=0x01, PrimaryDisplay=0x00, PrimaryDisplay_inst_2=0x00, PrimaryDisplay_inst_3=0x00")
    cli.CvProgKnobs("PcieSwEqOverride=0x01, PcieRootPortAspm_20=0x02, PcieRootPortDptp_20=0x05, PcieRootPortHPE_20=0x01, Rtd3Tbt=0x01, DiscreteTbtSupport=0x01")
    cli.CvProgKnobs("TbtVtdBaseSecurity=0x01, TbtBootOn=0x02, TrOsup=0x01, SecurityMode=0x01, TBTHotSMI=0x00, TBTHotNotify=0x00, Gpio5Filter=0x00, TBTSetClkReq=0x01")
    cli.CvProgKnobs("TbtLtr=0x01, TbtL1SubStates=0x00, Win10Support=0x02, DTbtController_0=0x01, DTbthostRouterPortNumber_0=0x02, DTbtPcieExtraBusRsvd_0=0x6A")
    cli.CvProgKnobs("DTbtPcieMemRsvd_0=0x02E1, DTbtPciePMemRsvd_0=0x04A0, CsmControl=0x01, BootOrder_3=0x0003, BootOrder_4=0x0002, BootOrder_5=0x0000, AfterEoP=0x00")
    echo_none = 'echo none_set_done > /root/bios_xml/next_step'
    os.system(echo_none)
    print 'set none_set_done into /root/bios_xml/next_step'
    #os.system('reboot')

def none_set_done(msg):
    print 'Access ' + msg
    echo_ddt_none = 'echo none_ddt > /root/bios_xml/next_step'
    os.system(echo_ddt_none)
    print 'set none_ddt into /root/bios_xml/next_step'
    print 'run none mode'
    print 'set user mode bios'
    set_bios_user()
    echo_user = 'echo user_set_done > /root/bios_xml/next_step'
    os.system(echo_user)
    #os.system('reboot')

def user_set_done(msg):
    print 'Access ' + msg
    echo_ddt_user = 'echo user_ddt > /root/bios_xml/next_step'
    os.system(echo_ddt_user)
    print 'set ddt_user into /root/bios_xml/next_step'
    print 'run user mode'
    print 'set secure mode bios'
    set_bios_secure
    echo_secure = 'echo secure_set_done > /root/bios_xml/next_step'
    os.system(echo_secure)
    #os.system('reboot')

def secure_set_done(msg):
    print msg

def dp_set_done(msg):
    print msg

def none_ddt(msg):
    print msg

def user_ddt(msg):
    print msg

def secure_ddt(msg):
    print msg

def dp_ddt(msg):
    print msg

def none_set_only(msg):
    print msg

def user_set_only(msg):
    print msg

def secure_set_only(msg):
    print msg

def dp_set_only(msg):
    print msg

def start(msg):
    print msg

def other(msg):
    print msg + 'try'

def notify_result(num, msg):
    numbers = {
        0 : none_set_done,
        1 : user_set_done,
        2 : secure_set_done,
        3 : dp_set_done,
        4 : none_ddt,
        5 : user_ddt,
        6 : secure_ddt,
        7 : dp_ddt,
        8 : none_set_only,
        9 : user_set_only,
        10 : secure_set_only,
        11 : dp_set_only,
        12 : start
    }

    method = numbers.get(num, other)
    if method:
        method(msg)

def test_ddt():
    all_set_txt = 'FOLDER_PATH'
    list_done_cmd = 'cat ' + FOLDER_PATH + '/next_step'
    next_step_info = os.popen(list_done_cmd).read()
    next_step_info = next_step_info.rstrip()
    print 'next_step_info:' + next_step_info
    notify_result(0, next_step_info)


if __name__ == "__main__":
    print "LINUX_VER:", LINUX_VER,"DATE:", DATE, "DDT_LOG:", DDT_LOG
    print "DDT_PATH: DDT_PATH"
    test_ddt()
