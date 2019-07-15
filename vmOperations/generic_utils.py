import logging

logger = logging.getLogger(__name__)

def validate_json(vm_object):
        #do validation and provide feedback if incorrect objects found
        print(vm_object)
        for vm in vm_object['vms']:
            print(vm['name'])
            'name' in vm
            if 'name' in vm:
                logger.debug('vm name key present : ')               
            else:
                logger.warning('vm name key not present')
                response = 'vm name key not present'
                exit()
            if 'template_uuid' in vm:
                    logger.debug('template_uuid key present')
            else:
                logger.warning('template_uuid key not present')
                exit()
            if 'memory_mb' in vm:
                    logger.debug('memory_mb key present')
            else:
                logger.warning('memory_mb key not present')
                exit()
            if 'cpu_sockets' in vm:
                    logger.debug('cpu_sockets key present')
            else:
                logger.warning('cpu_sockets key not present')
                exit()
            if 'datastore_cluster' in vm:
                    logger.debug('datastore_cluster key present')
            else:
                logger.warning('datastore_cluster key not present')
                exit()
            if 'template_moref' in vm:
                    logger.debug('template_moref key present')
            else:
                logger.warning('template_moref key not present')
                exit()
        response = "success"
        return response