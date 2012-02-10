#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
    Author: wg_koro
    License: MIT License

    This script provides easy login to EC2 Instances.

    Requirement:
    - Python 2.6 or later
    - boto package ('easy_install boto' or 'pip install boto')

    How to use -> Please see README
"""
import os
import boto
import boto.ec2
import sys
import traceback
from optparse import OptionParser

# Change these values ============================
SSH_DIR = '/Users/xxxxx/.ssh/'
DEFAULT_USER = 'ec2-user'
DEFAULT_PORT = 22
AWS_DATA = {
    'default'   : {
        'access_key'    : '',
        'secret_key'    : '',
        'region'        : 't',
    },
}
# ==============================================

VERSION = '1.0'

REGION = {
    't'     : 'ap-northeast-1', # TOKYO
    's'     : 'ap-southeast-1', # SINGAPORE
    'v'     : 'us-east-1', # US East(Virginia)
    'o'     : 'us-west-2', # US West(Oregon)
    'n'     : 'us-west-1', # US West(N. California)
    'e'     : 'eu-west-1', # EU West(Ireland)
    'sa'    : 'sa-east-1', # S. America(Sao Paulo)
}

COMMAND = 'ssh -i %(sshkey)s -p %(port)s %(user)s@%(server)s'


class EC2LoginHelper:
    def __init__(self):
        self.instance_list = {}


    def main(self, account, region, port):
        if not account in AWS_DATA:
            print 'Account not found!'
            return

        aws_data = AWS_DATA[account]
        self.port = port
        self._connect_ec2(aws_data, region)


    def _connect_ec2(self, aws_data, region):
        """
        make connection to EC2.
        """
        if region:
            region_name = REGION[region]
        else:
            region_name = REGION[aws_data['region']]

        print 'Connecting to EC2 (%s)...' % region_name
        try:
            if not aws_data['access_key']:
                self.conn = boto.ec2.connect_to_region(region_name=region_name)
            else:
                self.conn = boto.ec2.connect_to_region( region_name=region_name,
                        aws_access_key_id=aws_data['access_key'],
                        aws_secret_access_key=aws_data['secret_key']
                )
                
            reservations = self.conn.get_all_instances()
            instances = [i for r in reservations for i in r.instances]

            print '...Done.'
        except:
            print 'EC2 Connection Error!!\nTRACEBACK: %s' % traceback.format_exc()
            return

        self._show_instance_info(instances)


    def _show_instance_info(self, instances):
        """
        Show instance info.
        """
        info = '%(array_id)s: %(tag_name)s, %(dns)s, %(image_id)s, %(instance_id)s, key:%(ssh)s'
        if len(instances) < 1:
            print 'Instance not found.'
            return

        for i, v in enumerate(instances):
            if not v.public_dns_name:
                dns = '( Stopping )'
            else:
                dns = v.public_dns_name

            datas = {
                'array_id'  : i,
                'tag_name'  : v.tags.get('Name', '( No Name )'),
                'dns'       : dns,
                'image_id'  : v.image_id,
                'instance_id'   : v.id,
                'ssh'       : v.key_name,
            }
            if datas['ssh'].find('.pem') != -1:
                key_file = datas['ssh']
            else:
                key_file = '%s.pem' % datas['ssh']

            self.instance_list[i] = {
                'name'  : datas['tag_name'],
                'dns'   : datas['dns'],
                'key'   : key_file
            }

            print '-' * 60
            print info % datas

        print '-' * 60
        self._start_ssh()


    def _start_ssh(self):
        """
        Make SSH command and start SSH.
        """
        try:
            message = '\nEnter number you want to connect: '
            num = raw_input(message)
            while not int(num) in self.instance_list:
                num = raw_input(message)

            message_user = 'Enter username for ssh_login(blank = %s): ' % DEFAULT_USER 
            user = raw_input(message_user)
            if not user:
                user = DEFAULT_USER
            
            target = self.instance_list[int(num)]
            ssh_key_path = os.path.join(SSH_DIR, target['key'])
            if not os.path.exists(ssh_key_path):
                print 'SSH key not found! KEY_PATH[ %s ]' % ssh_key_path
                return

            command = COMMAND % {'sshkey' : ssh_key_path, 'user' : user, 'server' : target['dns'], 'port' : self.port}

            print 'Connecting to "%s"... [SSH COMMAND: %s ]' % (target['name'], command)
            os.system(command)
        except KeyboardInterrupt:
            print '\nAborted!'
        finally:
            sys.exit()





if __name__ == '__main__':
    lists = ', '.join([acc for acc in AWS_DATA.keys()])
    usage = u'%prog [account_name ( ' +lists +' )] [Option]\n'

    parser = OptionParser(usage=usage, version=VERSION)
    parser.add_option(
        '-p', '--port',
        action = 'store',
        type = 'int',
        dest = 'port',
        help = 'Specify port number'
    )
    parser.add_option(
        '-r', '--region',
        action = 'store',
        type = 'str',
        dest = 'region',
        help = 'Specify region. "t"->Tokyo "s"->Singapore "v"->US East(Virginia) "o"->US West(Oregon) "n"->US West(N. California) "e"->EU West(Ireland) "sa"->S. America(Sao Paulo)' 
    )
    parser.set_defaults(
        region = None,
        port = DEFAULT_PORT
    )

    options, args = parser.parse_args()
    region = options.region
    port = options.port

    count = len(args)
    if count < 1:
        account = 'default'
    elif count > 1:
        parser.error('Too many account!')
    else:
        account = args[0]

    if region:
        if not region in REGION:
            parser.error('Invalid region!')

    e = EC2LoginHelper()
    e.main(account, region, port)

