
import ssl
import logging
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from vcenter_utils import utils
import re

logger = logging.getLogger(__name__)


class VM(object):
    
    def __init__(self, vm_object):
        self.vm = vm_object
        logger.debug('Init with VM : ' + str(self.vm))
    
    def clone_template(self, si, template_uuid, template_moref, vm_name, datacenter, folder, cluster, resource_pool=None, datastore=None, dsc=None):
        """
        Clone VM from a template
        """
        obj_util = utils()
        if datacenter:
            dest_datacenter = obj_util.get_obj_moref(si, 'Datacenter', datacenter)
        else:
            print('No destination datacenter provided')
            exit()
        
        if folder:
            dest_folder = obj_util.get_obj_moref(si, 'Folder', folder)
        else:
            print('No destination folder specified')
            exit()
        if cluster:
            dest_cluster = obj_util.get_obj_moref(si, 'ClusterComputeResource', cluster)
        else:
            print('No destination cluster specified')
            exit()
        
        if template_uuid and template_moref:
            template = obj_util.get_vm_obj(si, template_uuid, template_moref)
        else:
            print('Missing template uuid or template vmid or both')
            exit()
        
        if resource_pool != None:
            resource_pool = obj_util.get_vm_obj(si, 'ResourcePool', resource_pool)
        else:
            resource_pool = dest_cluster.resourcePool

        if datastore != None:
            dest_datastore = obj_util.get_obj_moref(si, 'Datastore', datastore)
        else:
            print('No destination datastore. Assuming DatastoreCluster')
            pass
        
        vmconf = vim.vm.ConfigSpec()

        if dsc != None:
            podsel = vim.storageDrs.PodSelectionSpec()
            pod = obj_util.get_obj_moref(si, 'StoragePod', dsc)
            podsel.storagePod = pod

            storagespec = vim.storageDrs.StoragePlacementSpec()
            storagespec.podSelectionSpec = podsel
            #should this be create or clone?
            storagespec.type = 'create'
            storagespec.folder = dest_folder
            storagespec.resourcePool = resource_pool
            storagespec.configSpec = vmconf
        else:
            print('No DSC passed')
            pass
        
        try:
            rec = si.storageResourceManager.RecommendDatastores(storageSpec=storagespec)
            print('pause here')
            rec_action = rec.recommendations[0].action[0]
            real_datastore = rec_action.destination._moId
        except:
            real_datastore = template.datastore[0]._moId

        datastore = obj_util.get_obj_moref(si, 'Datastore', real_datastore)
        
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        devicespec = vim.vm.device.VirtualDeviceSpec()


        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.powerOn = False
        resource = template.CloneVM_Task(folder=dest_folder, name=vm_name, spec=clonespec)
        return resource
    
    def flex_vm_memory(self, si, vm, mb, reserv=None):
        #flex vm memory
        #check if hotadd is enabled
        mb = int(mb)
        logger.debug('HotAdd set to : ' + str(vm.config.memoryHotAddEnabled))
        #create the config spec
        config_spec = vim.vm.ConfigSpec()
        if vm.config.memoryHotAddEnabled == True or vm.runtime.powerState == 'poweredOff':
            if reserv != None:
                reservraw = mb / 100 * int(reserv)
                reserv = int(reservraw)
                logger.debug('Reservation percentage requested : ' + str(reserv) + 'Actual reservation to be set is : ' + str(reservraw))
                resource_allocation_spec = vim.ResourceAllocationInfo()
                resource_allocation_spec.limit = mb
                resource_allocation_spec.reservation = reserv
                config_spec.memoryAllocation = resource_allocation_spec
            #Set memory
            config_spec.memoryMB = mb
            try:
                response = vm.ReconfigVM_Task(config_spec)
            except:
                logger.exception('Exception reconfiguring VM for memory flex')
        elif vm.config.memoryHotAddEnabled == False and vm.runtime.powerState == 'poweredOn':
            logger.warning('Memory HotAdd is currently disabled and VM is powered on, unable to update VM')
            exit()
            pass
        else:
            logger.warning('Hot add state not found, VM object may be incorrect')
            pass
        return response

    def flex_vm_cpu(self, si, vm, cpu, core=None, mhz=None, reserv=None):
        #flex vm memory
        # add check if hotadd is enabled
        cpu = int(cpu)
        if core != None:
          core = int(core)
        if vm.config.cpuHotAddEnabled == True or vm.runtime.powerState == 'poweredOff':
            resource_allocation_spec = vim.ResourceAllocationInfo()
            if reserv != None and mhz != None:
                reservraw = mhz / 100 * reserv
                reserv = int(reservraw)
                resource_allocation_spec.reservation = reserv
            elif reserv != None and mhz == None:
                print('Must specify both reservation and mhz')
            else:
                pass

            if mhz != None:
                resource_allocation_spec.limit = mhz
            else:
                pass
            
            config_spec = vim.vm.ConfigSpec()
            # this makes it pass to else for some reason
            if core != None and vm.runtime.powerState == 'poweredOn':
                print('VM must be powered off for cpu core changes')
            elif core != None and vm.runtime.powerState == 'poweredOff':
                config_spec.numCoresPerSocket = core
            else:
                pass

            config_spec.numCPUs = cpu
            config_spec.cpuAllocation = resource_allocation_spec
            task = vm.ReconfigVM_Task(config_spec)
            response = task
        elif vm.config.cpuHotAddEnabled == False and vm.runtime.powerState == 'poweredOn':
            print('CPU HotAdd is currently disabled and VM is powered on, unable to update VM')
            response = 'Failed'
            pass
        else:
            print('Somethings not right')
            pass
        return response

    def add_vm_disk(self, si, vm, disk_size, disk_type, bus=None, unit=None, controller_type=None):

        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        if unit == None:
            unit_number = 0
        for dev in vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    print("we don't support this many disks")
                    return
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        # add disk here
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        spec.deviceChange = [disk_spec]
        resource = vm.ReconfigVM_Task(spec=spec)
        print("%sGB disk added to %s" % (disk_size, vm.config.name))
        return resource

    def del_vm_disk(self, si, vm, disk_uuid):

        #hdd_label = hdd_prefix_label + str(disk_number)
        virtual_hdd_device = None
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.deviceInfo.label == hdd_label:
                virtual_hdd_device = dev
        if not virtual_hdd_device:
            raise RuntimeError('Virtual {} could not be found.'.format(virtual_hdd_device))

        virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_hdd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        virtual_hdd_spec.device = virtual_hdd_device

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [virtual_hdd_spec]
        task = vm.ReconfigVM_Task(spec=spec)
        return task

    def extend_vm_disk(self, si, vm, disk_uuid, disk_size):
        ''' 
        Extends disk attached to VM
        '''

        disk_size_kb = int(disk_size) * 1024 * 1024
        virtual_hdd_device = None
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) and dev.backing.uuid == disk_uuid:
                logger.debug('Disk found for UUID : ' + disk_uuid)
                virtual_hdd_device = dev
        if not virtual_hdd_device:
            logger.exception('Virtual {} could not be found.'.format(virtual_hdd_device))

        virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_hdd_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        virtual_hdd_device.capacityInKB = disk_size_kb
        virtual_hdd_spec.device = virtual_hdd_device

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [virtual_hdd_spec]
        try:
            logger.info('Performing reconfigure VM for disk extension')
            resource = vm.ReconfigVM_Task(spec=spec)
        except:
            logger.exception('Exception while reconfiguring VM')

        return resource

    def add_vm_controller(self, si, vm, bus=None, controller_type=None, sharing=None):
        """
        Adds a controller to a VM
        
        parameter bus accepts : 
        0-3
        
        parameter sharing accepts:
        physicalSharing, virtualSharing, and noSharing
        

        """
        #Create initial configspec
        spec = vim.vm.ConfigSpec()
        #create a controller list to make the check for existing devices easier
        controller_list = [
        vim.vm.device.VirtualLsiLogicSASController
        , vim.vm.device.ParaVirtualSCSIController
        , vim.vm.device.VirtualLsiLogicController
        , vim.vm.device.VirtualBusLogicController]
        bus_list = []
        for dev in vm.config.hardware.device:
            for ctrl in controller_list:
              if isinstance(dev, ctrl):
                  virtual_controller = dev
                  print('Device Found : ' + ctrl._wsdlName + ' on BUS ID : ' + str(dev.busNumber))
                  bus_list.append(dev.busNumber)
                  print(bus_list)
                  if bus != None:
                      if bus == dev.busNumber:
                          print('Controller already found on BUS ID : ' +str(dev.busNumber))
                          exit()
                      elif bus > 3 or bus < 0:
                          print('BUS ID providers is not supported, must be between 0 and 3')
                          exit()      
              else:
                  print('Device Not Found')
                  pass
        #Create the virtual device spec
        device_spec = vim.vm.device.VirtualDeviceSpec()
        #Create the specific controller device - note this is a data object extension of VirtualController
        device_spec_virtualdevice = vim.vm.device.VirtualLsiLogicSASController(hotAddRemove=True, sharedBus=sharing)
        device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        #TIL properties are inherited from the higher level data objects
        device_spec_virtualdevice.busNumber = bus
        device_spec.device = device_spec_virtualdevice
        spec.deviceChange = [device_spec]
        try:
            logger.info('Performing VM Reconfiguration task for adding a disk controller')
            resource = vm.ReconfigVM_Task(spec=spec)
        except:
            logger.exception('Exception for VM Reconfiguration for disk controller')
        return resource
    
    def set_vm_network(self, si, vm, nic_id, network_moref, nic_type=None, connected=None, connect_on_startup=None):
        nic_map = {
            1 : "Network Adaptor 1",
            2 : "Network Adaptor 2",
            3 : "Network Adaptor 3",
            4 : "Network Adaptor 4",
            5 : "Network Adaptor 5",
            6 : "Network Adaptor 6",
            7 : "Network Adaptor 7",
            8 : "Network Adaptor 8",
            9 : "Network Adaptor 9",
            10 : "Network Adaptor 10"
        }
        #regex to check network type
        p = re.compile('[dvportgroup-]')
        q = re.compile('[network-]')
        obj_util = utils()
        #get network object  
        try:
            logger.debug('Get network object from : ' + network_moref)
            if p.match(network_moref):
                network_type = 'DistributedVirtualPortgroup'
                #set network object
                network = obj_util.get_obj_moref(si, network_type, network_moref)
                logger.debug('Network is of type : ' + network._wsdlName)
                logger.debug('Network name is : ' + network.name)
                dvs = network.config.distributedVirtualSwitch
            elif q.match(network_moref):
                network_type = 'Network'
                #set network object
                network = obj_util.get_obj_moref(si, network_type, network_moref)
                logger.debug('Network is of type : ' + network._wsdlName)
                logger.debug('Network name is : ' + network.name)
            else:
                logger.warning('no matching network type found for : ' + network_moref)
                exit()
        except:
            logger.exception('exception getting network object : ' + network_moref)
            exit()

        #iterate through devices looking for type VirtualEthernetCard
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                #use the dict to get the correct card 
                for key, value in nic_map.items():
                    if key == int(nic_id):
                        logger.debug('Network adaptor is : ' + value)
                        virtual_nic_device = dev
                        virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
                        virtual_nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        virtual_nic_spec.device = virtual_nic_device
                        if network._wsdlName == 'DistributedVirtualPortgroup':
                            logger.debug('Setting data objects for : ' + network._wsdlName)
                            virtual_nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                            virtual_nic_spec.device.backing.port = vim.dvs.PortConnection()
                            virtual_nic_spec.device.backing.port.portgroupKey = network_moref
                            virtual_nic_spec.device.backing.port.switchUuid = dvs.uuid
                        elif network._wsdlName == 'Network':
                            if isinstance(network, vim.OpaqueNetwork):
                                logger.debug('Setting data objects for Opaque network: ' + network._wsdlName)
                                virtual_nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
                                virtual_nic_spec.device.backing.opaqueNetworkType = network.summary.opaqueNetworkType
                                virtual_nic_spec.device.backing.opaqueNetworkId = network.summary.opaqueNetworkId
                            else:
                                logger.debug('Setting data objects for : ' + network._wsdlName)
                                virtual_nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                                virtual_nic_spec.device.backing.useAutoDetect = False
                                virtual_nic_spec.device.backing.deviceName = network.name
                        #build spec data objects
                        spec = vim.vm.ConfigSpec()
                        spec.deviceChange = [virtual_nic_spec]
                        try:
                            #attempt to reconfigure VM with spec and get task object back
                            logger.info('Performing VM Reconfiguration task for setting network')
                            resource = vm.ReconfigVM_Task(spec=spec)
                            break
                        except:
                            logger.exception('Exception performing VM reconfigure task')
                            exit()
                    else:
                        logger.debug('no matching nic id found for value : ' + value)
                        pass
        return resource

    def set_vm_extraconfig(self, si, vm, config_dict):
        '''
        Takes a dictionary of key values for extra config properties against a virtual machine and applies them.
        '''
        #Create the vm configspec
        spec = vim.vm.ConfigSpec()
        options = []
        for key, value in config_dict.items():
            #Create the vim data object for extraConfig
            extra_config = vim.option.OptionValue()
            logger.debug('Key value is : ' + key)
            extra_config.key = key
            logger.debug('Value is : ' + value)
            extra_config.value = value
            #append each key/value pair to the options array
            options.append(extra_config)
        
        logger.debug(options)
        spec.extraConfig = options
        try:
            logger.info('Performing VM Reconfiguration task for extraConfig options')
            resource = vm.ReconfigVM_Task(spec=spec)
        except:
            logger.exception('VM Reconfiguration failed')
            exit()
        return resource
