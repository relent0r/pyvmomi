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

with open(args.jsoninput) as cfg:
    vm_json = json.load(cfg)
    cfg.close()
    print(cfg)


jsonvalidate = validate_json(vm_json)
print(jsonvalidate)
obj_utils = utils()
si = obj_utils.si_instance(args.host, args.user, args.password, args.port)

def build_vms(vm_json):
   '''
   Function for triggered the creation of VM's based on json input
   '''
   for vm in vm_json['vms']:
       vm_name = vm['name'] 
       template_uuid = vm['template_uuid']
       template_moref = vm['template_moref']
       datacenter = vm['datacenter']
       dest_folder = vm['dest_folder']
       dest_cluster = vm['dest_cluster']
       cpu_sockets = vm['cpu_sockets']
       memory_mb = vm['memory_mb']
       memory_reservation = vm['reservation']
       datastore_cluster = vm['datastore_cluster']
       nics = vm['nics']
       vmbuild = VirtualMachine.VM(vm_json)
       build_task = vmbuild.clone_template(si, template_uuid, template_moref, vm_name, datacenter, dest_folder, dest_cluster, dsc=datastore_cluster)
       obj_utils = utils()
       # Wait for task to finish and validate success or exit of build failed
       build_task_resource = obj_utils.wait_for_task(build_task)
       if build_task.info.state == 'success':
           logger.debug('VM ' + vm_name + ' built')
       else:
          logger.warning('Task result is : ' + build_task.info.state)
          logger.warning('VM Clone failed')
          exit()
       # Perform CPU flex and wait for task completion
       cpu_task = vmbuild.flex_vm_cpu(si, build_task_resource, cpu_sockets)
       cpu_task_resource = obj_utils.wait_for_task(cpu_task)
       logger.debug('cpu task complete for vm : ' + vm_name)
       if build_task.info.state == 'success':
           logger.debug('CPU Flex on ' + vm_name + ' complete')
       else:
          logger.warning('Task result is : ' + cpu_task.info.state)
          logger.warning('CPU flex failed')
       
       memory_task = vmbuild.flex_vm_memory(si, build_task_resource, memory_mb, reserv=memory_reservation)
       memory_task_resource = obj_utils.wait_for_task(memory_task)
       logger.debug('memory task complete for vm : ' + vm_name)
       if build_task.info.state == 'success':
           logger.debug('Memory Flex on ' + vm_name + ' complete')
       else:
          logger.warning('Task result is : ' + memory_task.info.state)
          logger.warning('Memory flex failed')
       for nic in nics:
          logger.debug('Set Network Adaptor :' + nic['adaptor_number'])
          nic_id = nic['adaptor_number']
          network_moref = nic['network']
          nic_task = vmbuild.set_vm_network(si, build_task_resource, nic_id, network_moref)
          nic_task_resource = obj_utils.wait_for_task(nic_task)
          if nic_task.info.state == 'success':
            logger.debug('Network adaptor change on ' + vm_name + ' complete')
          else:
            logger.warning('Task result is : ' + nic_task.info.state)
            logger.warning('Network Adaptor Set Failed')
       power_task = vmbuild.set_vm_power(si, build_task_resource, vm['state'])
       power_task_resource = obj_utils.wait_for_task(power_task)
       logger.debug('power task complete for vm : ' + vm_name)
   print('build complete')

if validate_json(vm_json) == 'success':
   logger.debug('Json is validated successfully')
   build_vms(vm_json)




logger.debug('Build Finished')
