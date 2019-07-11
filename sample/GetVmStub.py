from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl, VmomiSupport

import argparse
import atexit
import getpass
import sys
import ssl

def GetArgs():
   """
   Supports the command-line arguments listed below.
   """

   parser = argparse.ArgumentParser(description='Process args for powering on a Virtual Machine')
   parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store', help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=False, action='store', help='Password to use when connecting to host')
   parser.add_argument('-v', '--vmid', required=True, action='store', help='ID of the Virtual Machines to power on')
   args = parser.parse_args()
   return args

args = GetArgs()
vmid = args.vmid

context = None
if hasattr(ssl, '_create_unverified_context'):
    context = ssl._create_unverified_context()
si = SmartConnect(host=args.host,
                        user=args.user,
                        pwd=args.password,
                        port=int(args.port),
                        sslContext=context)

vm_obj = VmomiSupport.GetWsdlType('urn:vim25', 'VirtualMachine')(vmid, si._stub)
print(vm_obj.name)