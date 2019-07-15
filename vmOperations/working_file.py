import argparse
import VirtualMachine
from vcenter_utils import utils
from generic_utils import validate_json
import json
import ast
from collections import namedtuple
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def GetArgs():
   """
   Supports the command-line arguments listed below.
   """

   parser = argparse.ArgumentParser(description='Process args for powering on a Virtual Machine')
   parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to')
   parser.add_argument('-o', '--port', type=int, default=443, action='store', help='Port to connect on')
   parser.add_argument('-u', '--user', required=True, action='store', help='User name to use when connecting to host')
   parser.add_argument('-p', '--password', required=True, action='store', help='Password to use when connecting to host')
   parser.add_argument('-y', '--jsoninput', required=True, action='store', help='ID of the Virtual Machines to power on')
   args = parser.parse_args()
   return args
args = GetArgs()
print(args.port)
template_moref = 'vm-53938'
#args.jsoninput = '{"vms": [{"name": "test3", "template_uuid": "502b5bde-18a3-538d-8112-7afc44827d39", "description": "This is VM1", "ip_allocation_mode": "pool", "needs_customization": "false", "memory": "2048"}, {"name": "VM2", "template_uuid": "93b82b05-aa18-43ef-ab9e-f0a622beb8e8", "description": "This is VM2", "ip_allocation_mode": "pool", "needs_customization": "false", "memory": "1024"}]}'
with open(args.jsoninput) as cfg:
    vm_json = json.load(cfg)
    # vm_object = namedtuple('ConfigObject', cfg.keys())(**cfg)
    cfg.close()
    print(cfg)

#cfg = json.loads(args.jsoninput)
#vmbuild = VirtualMachine.VM(vm_object)
jsonvalidate = validate_json(vm_json)
print(jsonvalidate)
obj_utils = utils()
si = obj_utils.si_instance(args.host, args.user, args.password, args.port)

if validate_json(vm_json) == 'success':
   print('Json is validated ok')
   def build_vms(vm_json)
       for vm in vm_json['vms']:
           vm_name = vm['name'] 
           template_uuid = vm['template_uuid']
           template_moref = vm['template_moref']
           datacenter = vm['datacenter']
           cpu_sockets = vm['cpu_sockets']
           memory_mb = vm['memory_mb']
           datastore_cluster = vm['datastore_cluster']
           for nic in vm['nics']
               adaptor_number = nic['adaptor_number']
               ip_address = nic['ip_address']
               adaptor_type = adaptor_type['adaptor_type']



#vm = obj_utils.get_vm_obj(si, template_uuid, template_moref)
memory = 2048
cpu = 4
reserv = 80
mhz = 2000
cores = 1
bus = 1
scsi_sharing = 'noSharing'
datacenter = 'datacenter-561'
vm_folder = 'group-v42447'
dsc = 'group-p40141'
cluster = 'domain-c38746'
#network = 'network-24564'
network = 'dvportgroup-16817'
#try:
#    reconfig = vmbuild.flex_vm_memory(si, vm_object, memory, reserv)
#    if reconfig == False:
#        print('Memory Upgrade Failed')
#    else:
#        print(reconfig.moid)
#except Exception as e:
#   print('Exception')

#try:
#    reconfig = vmbuild.flex_vm_cpu(si, vm_object, cpu, core=cores, mhz=mhz, reserv=reserv)
#except Exception as e:
#   print('Exception :', e)

#try:
#    disk_add = vmbuild.add_vm_disk(si, vm_object, 6, 'thick')
#except Exception as e:
#   print('Exception :', e)
#try:
#    controller_add = vmbuild.add_vm_controller(si, vm_object, bus=bus, sharing=scsi_sharing)
#except Exception as e:
#   print('Exception :', e)

       
#print(template_uuid)
#datastore = obj_utils.get_obj_moref(si, 'Datastore', 'datastore-43227')
#print('Datastore ID is ' + str(datastore._moId))
#template = obj_utils.get_vm_obj(si, template_uuid, template_moref)
#vmbuild.clone_template(si, template_uuid, template_moref, vm_name, datacenter, vm_folder, cluster, dsc=dsc)
#task = vmbuild.set_vm_network(si, vm, 1, network)
#configdict = {
#   'testkey1': 'testvalue1',
#   'testkey2': 'testvalue2'
#}
#vmbuild.set_vm_extraconfig(si, vm, configdict)
#diskid = '6000C292-3659-9abc-94f8-d7305e30d8c9'
#vmbuild.extend_vm_disk(si, vm, diskid, 20)
print('done')
#vmbuild.create_vms(si, vm_object)