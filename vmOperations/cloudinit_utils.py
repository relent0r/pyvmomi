import logging

logger = logging.getLogger(__name__)

def validate_json(cloudinit_object):
    if 'configdata' in cloudinit:
        # guestinfo.cloud-init.config.data
        logger.debug('configdata key present : ')               
    else:
        logger.warning('configdata key not present')
        response = 'configdata key not present'
        exit()
    if 'encoding' in cloudinit:
        # guestinfo.cloud-init.data.encoding
        logger.debug('encoding key present : ')               
    else:
        logger.warning('encoding key not present')
        response = 'encoding key not present'
        exit()
    if 'domain' in cloudinit:
        # guestinfo.dns.domain
        logger.debug('domain key present : ')               
    else:
        logger.warning('domain key not present')
        response = 'domain key not present'
        exit()
    if 'hostname' in cloudinit:
        # guestinfo.hostname
        logger.debug('hostname key present : ')               
    else:
        logger.warning('hostname key not present')
        response = 'hostname key not present'
        exit()
    for interface in cloudinit.interfaces
        if 'dhcp' in interface:
            # guestinfo.interface.0.dhcp
            logger.debug('dhcp key present : ')               
        else:
            logger.warning('dhcp key not present')
            response = 'dhcp key not present'
            exit()
        if 'ipaddress' in interface:
            # guestinfo.interface.0.ip.0.address
            logger.debug('ipaddress key present : ')               
        else:
            logger.warning('ipaddress key not present')
            response = 'ipaddress key not present'
            exit()
        if 'gateway' in interface:
            # guestinfo.interface.0.route.0.gateway
            logger.debug('gateway key present : ')               
        else:
            logger.warning('gateway key not present')
            response = 'gateway key not present'
            exit()