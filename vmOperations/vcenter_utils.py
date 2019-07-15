from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl, VmomiSupport

import argparse
import atexit
import getpass
import sys
import ssl
import logging

logger = logging.getLogger(__name__)

class utils():
    def si_instance(self, host, username, password, port):
            context = None
            if hasattr(ssl, '_create_unverified_context'):
                context = ssl._create_unverified_context()
            si = SmartConnect(host=host,
                            user=username,
                            pwd=password,
                            port=port,
                            sslContext=context)
            return si

    def get_obj_moref(self, si, obj_type, moid):
        
        obj = VmomiSupport.GetWsdlType('urn:vim25', obj_type)(moid, si._stub)
        return obj
    
    def get_vm_obj(self, si, object_uuid, object_moref):
        search_index = si.content.searchIndex
        try:
            vm = search_index.FindByUuid(datacenter=None , uuid=object_uuid , instanceUuid=True , vmSearch=True)
        except:
            logger.warning('Exception querying search index on vCenter')
        try:
            if vm._moId == object_moref:
               print(vm.name)
               resource = vm
            else:
                print('VMID or UUID do not match VM')
                exit()
        except AttributeError:
            logger.warning('VM was unable to be found by Instance UUID')
            exit()
        return resource

    def wait_for_task(self, task):
        """ 
        wait for a vCenter task to finish 
        """
        task_done = False
        while not task_done:
            if task.info.state == 'success':
                logger.debug('Task completed with success')
                return task.info.result

            if task.info.state == 'error':
                logger.warning('Task completed with error')
                task_done = True
