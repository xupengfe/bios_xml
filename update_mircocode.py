#!/bin/python

'''
If bios not specified, read BIOS from system
update the patch and load it back on the system
'''
def update_microcode(patch, bios=None):
    import os, sys
    import shlex, subprocess
    import misc.XmlCli.XmlCli as cli

    if sys.platform not in ['win32', 'cygwin']:
        raise Exception('update_microcode is only supported on Windows')

    if not os.path.exists(patch):
        raise Exception('Patch %s does not seem to be accessible'%patch)

    romulator = False
    romulator_path = r'c:\program files (x86)\DediProg\EM100'
    if sys.platform != 'win32':
        romulator_path = romulator_path.replace('\\', os.path.sep)
    if os.path.exists(romulator_path):
        romulator = True
        command_line = [os.path.join(romulator_path, 'smucmd.exe')]
        args = '-c'
        args = shlex.split(args)
        p = subprocess.Popen(command_line + args, stdout=subprocess.PIPE)
        for line in p.stdout.readlines():
            if 'No device is connected' in line:
                romulator = False

    if romulator: # We have to read BIOS to update it
        if not bios:
            print('Reading current BIOS as template...')
            bios = r'C:\\TEMP\\last_bios.bin'
            if sys.platform != 'win32':
                bios = bios.replace('\\', os.path.sep)
            if os.path.exists(bios):  os.remove(bios)
            args = r'--stop --set W25Q256FV -r %s --start'%bios
            args = shlex.split(args)
            p = subprocess.Popen(command_line + args, stdout=subprocess.PIPE)
            p.wait()
            if p.returncode != 0x0:
                raise Exception('Unable to read BIOS from romulator')
            if not os.path.exists(bios):
                raise Exception('Unable to read BIOS from romulator')

    if bios: # Either we read it from the system or it was passed in
        newbios = r'C:\\TEMP\\new_bios.bin'
        newbiosempty = r'C:\\TEMP\\new_bios_empty.bin'
        if sys.platform != 'win32':
            newbios = newbios.replace('\\', os.path.sep)
            newbiosempty = newbiosempty.replace('\\', os.path.sep)
        if os.path.exists(newbios):  os.remove(newbios)
        if os.path.exists(newbiosempty):  os.remove(newbiosempty)
        # Update the BIOS with the new patch
        #error = cli.ProcessUcode('delete', bios, patch, outPath=newbiosempty, PrintEn=False)
        #if not error: error |= cli.ProcessUcode('update', newbiosempty, bios, patch, outPath=newbios, PrintEn=False)
        #else: error = cli.ProcessUcode('update', bios, patch, outPath=newbios, PrintEn=False)
        error = cli.ProcessUcode('update', bios, patch, outPath=newbios, PrintEn=False)
        if error != 0:
            raise Exception('Unable to change patch; likely original BIOS is malformed')
        if not os.path.exists(newbios):
            cli.ProcessUcode('READ', bios)
            raise Exception('Unable to read BIOS that has new patch: %s'%newbios)
        cli.ProcessUcode('READ', newbios)

        if romulator:
            print('Loading BIOS with new patch...')
            prog_result = False
            args = r'--stop --set W25Q256FV -d %s -v --start'%newbios
            args = shlex.split(args)
            p = subprocess.Popen(command_line + args, stdout=subprocess.PIPE)
            for line in p.stdout.readlines():
                if 'Verify Pass' in line:
                    prog_result = True
                if 'elapsed' not in line:
                    print(line.strip())
            p.wait()
            if p.returncode == 0x0:
                prog_result = True
        else:
            raise Exception('Full BIOS update via CLI is not yet supported')
    else:
        error = cli.ProcessUcode('update', 0, patch, PrintEn=False)
        if error != 0:
            raise Exception('Unable to change patch via BIOS CLI')
        prog_result = True
        cli.ProcessUcode('READ', 0)

    return prog_result

if __name__ == '__main__':
    import sys
    if (len(sys.argv) < 2):
        raise Exception('Patch not provided as first argument')
    else:
        patch = sys.argv[1]

    if update_microcode(patch):
        sys.exit(0)
    else:
        sys.exit(1)
