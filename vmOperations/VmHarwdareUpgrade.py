"""
Python program for powering on vms on a host on which hostd is running
"""

from __future__ import print_function

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl

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
   parser.add_argument('-i', '--uuid', required=True, action='store', help='InstanceUuid of the virtual machine')
   parser.add_argument('-x', '--vmver', required=True, action='store', help='Hardware Version to upgrade to')
   args = parser.parse_args()
   return args

args = GetArgs()
vmid = args.vmid
vmx = args.vmver
uuid = args.uuid

print(vmx)
context = None
if hasattr(ssl, '_create_unverified_context'):
    context = ssl._create_unverified_context()
si = SmartConnect(host=args.host,
                        user=args.user,
                        pwd=args.password,
                        port=int(args.port),
                        sslContext=context)

def upgrade_hardware(self, vmid , uuid , vmxversion):
    search_index = si.content.searchIndex
    vm = search_index.FindByUuid(datacenter=None , uuid=uuid , instanceUuid=True , vmSearch=True)
    if vm._moId == vmid:
       print(vm.name)
       tasks = vm.UpgradeVM_Task(version=vmx)
    else:
        print('VMID and UUID do not match VM')
        pass
    return tasks

def WaitForTasks(tasks, si):
   """
   Given the service instance si and tasks, it returns after all the
   tasks are complete
   """

   pc = si.content.propertyCollector

   taskList = [str(task) for task in tasks]

   # Create filter
   objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                                                            for task in tasks]
   propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                         pathSet=[], all=True)
   filterSpec = vmodl.query.PropertyCollector.FilterSpec()
   filterSpec.objectSet = objSpecs
   filterSpec.propSet = [propSpec]
   filter = pc.CreateFilter(filterSpec, True)

   try:
      version, state = None, None

      # Loop looking for updates till the state moves to a completed state.
      while len(taskList):
         update = pc.WaitForUpdates(version)
         for filterSet in update.filterSet:
            for objSet in filterSet.objectSet:
               task = objSet.obj
               for change in objSet.changeSet:
                  if change.name == 'info':
                     state = change.val.state
                  elif change.name == 'info.state':
                     state = change.val
                  else:
                     continue

                  if not str(task) in taskList:
                     continue

                  if state == vim.TaskInfo.State.success:
                     # Remove task from taskList
                     taskList.remove(str(task))
                  elif state == vim.TaskInfo.State.error:
                     raise task.info.error
         # Move to next version
         version = update.version
   finally:
      if filter:
         filter.Destroy()


task = upgrade_hardware(si , vmid , uuid , vmx)
WaitForTasks(task, si)
if task.info.state == 'error':
    print('Task has failed')
else:
    print('Task state is : ' + task.info.state)

print("Task ID is : " + 'task')
atexit.register(Disconnect, si)