
import os, sys, getopt
XML_PATH = '/root/bios_xml/'
XML_FILE = '/root/target.xml'

def get_xml():
    sys.path.append(r"%s"%(XML_PATH))
    import XmlCli as cli
    cli.clb._setCliAccess("linux")
    cli.clb.ConfXmlCli()
    cli.savexml(r"%s"%(XML_FILE))


def set_bios(bios_items):
    sys.path.append(r"%s"%(XML_PATH))
    import XmlCli as cli
    cli.clb._setCliAccess("linux")
    cli.clb.ConfXmlCli()
    cli.CvProgKnobs("%s"%(bios_items))
    print 'Set ' + bios_items + ' done.'

def main(argv):
    bios_set_items = ''
    try:
        opts, args = getopt.getopt(argv, "hgs:", ["bios_set_items="])

    except getopt.GetoptError:
        print 'Error: requestTest.py -g | -s "SecurityMode=0x00, TBTHotSMI=0x00"'
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print sys.argv[0] + ' -g | -s "SecurityMode=0x00, TBTHotSMI=0x00"'
            sys.exit()

        elif opt in ("-g", "--gId"):
            print 'Get xmli:'
            get_xml()
        elif opt in ("-s", "--sId"):
            bios_set_items = arg
            print 'Set bios items:' + bios_set_items
            set_bios(bios_set_items)

if __name__ == "__main__":
    main(sys.argv[1:])
