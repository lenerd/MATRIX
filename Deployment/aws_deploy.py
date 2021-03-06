import os
import json
import time
import boto3
import botocore

from random import shuffle
from datetime import datetime, timedelta
from pathlib import Path
from botocore import exceptions
from collections import OrderedDict

from Deployment.deploy import DeployCP


class AmazonCP(DeployCP):
    """
    The class enables deployment to AWS. All the methods are valid only to AWS
    Sub class of Deployment.DeployCP
    """
    def __init__(self, protocol_config):
        """
        :type protocol_config str
        :param protocol_config: the configuration of the protocol we want to deploy
        """
        super(AmazonCP, self).__init__(protocol_config)
        profile_name = 'default'
        if 'profileName' in self.protocol_config['cloudProviders']['AWS']:
            profile_name = self.protocol_config['cloudProviders']['AWS']['profileName']
        self.session = boto3.session.Session(profile_name=profile_name)

    def create_key_pair(self):
        """
        Creates private key file
        :return:
        """
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print('Creating key pairs', file=output_file)
            for regions_idx in range(len(regions)):
                client = self.session.client('ec2', region_name=regions[regions_idx][:-1])
                keys = client.describe_key_pairs()
                number_of_current_keys = len(keys['KeyPairs'])
                try:
                    key_idx = number_of_current_keys + 1
                    key_pair = client.create_key_pair(KeyName=f"Matrix{regions[regions_idx].replace('-', '')[:-1]}"
                                                              f"-{key_idx}")
                    key_name = key_pair['KeyName']
                    try:
                        with open(f'{Path.home()}/Keys/{key_name}', 'w+') as key_file:
                            key_file.write(key_pair['KeyMaterial'])
                    except EnvironmentError:
                        print('Cannot write the key to file', file=output_file)
                except botocore.exceptions.EndpointConnectionError as e:
                    print(e.response['Error']['Message'].upper(), file=output_file)
                except botocore.exceptions.ClientError as e:
                    print(e.response['Error']['Message'].upper(), file=output_file)
            print('Done creating key pairs, you will redirect to the deployment in few seconds..', file=output_file)
            time.sleep(5)

    def create_security_group(self):
        """
        Creates firewall rules
        :return:
        """
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print('Creating security groups', file=output_file)
            for idx in range(len(regions)):
                region_name = regions[idx][:-1]
                client = self.session.client('ec2', region_name=region_name)
                # create security group
                try:
                    response = client.create_security_group(
                        Description='Matrix system security group',
                        GroupName=f"MatrixSG{regions[idx].replace('-', '')[:-1]}",
                        DryRun=False
                    )
                    # Add FW rules
                    sg_id = response['GroupId']
                    ec2 = self.session.resource('ec2', region_name=region_name)
                    security_group = ec2.SecurityGroup(sg_id)
                    security_group.authorize_ingress(IpProtocol='tcp', CidrIp='0.0.0.0/0', FromPort=0, ToPort=65535)
                except botocore.exceptions.EndpointConnectionError as e:
                    print(e.response['Error']['Message'].upper(), file=output_file)
                except botocore.exceptions.ClientError as e:
                    print(e.response['Error']['Message'].upper(), file=output_file)
            print('Done creating security groups, you will redirect to the deployment in few seconds..',
                  file=output_file)
            time.sleep(5)

    def check_latest_price(self, instance_type, region):
        """
        Check what is the latest winning price for spot requests
        :type instance_type str
        :param instance_type: the type of the machines the protocol uses
        :type region str
        :param region: the regions that the instances are located
        :return: the last wining price
        """
        client = self.session.client('ec2', region_name=region[:-1])
        prices = client.describe_spot_price_history(InstanceTypes=[instance_type], MaxResults=1,
                                                    ProductDescriptions=['Linux/UNIX (Amazon VPC)'],
                                                    AvailabilityZone=region)
        return float(prices['SpotPriceHistory'][0]['SpotPrice'])

    def cancel_spot_requests(self):
        regions = self.protocol_config['cloudProviders']['AWS']['regions']
        for region in regions:
            instances = self.describe_instances(region[:-1], self.protocol_name)
            client = self.session.client('ec2', region_name=region[:-1])
            try:
                client.cancel_spot_instance_requests(SpotInstanceRequestIds=instances)
            except botocore.exceptions.ClientError as e:
                print(e.response['Error']['Message'].upper())

    def get_ami_disk_size(self, region_name):
        """
        :type region_name str
        :param region_name: the region that the instances are located
        :return: the size of the AMI disk
        """
        client = self.session.client('ec2', region_name)

        try:
            with open(f'{os.getcwd()}/GlobalConfigurations/awsRegions.json') as gc_file:
                global_config = json.load(gc_file, object_pairs_hook=OrderedDict)
        except EnvironmentError:
            print('Cannot open Global Configurations')

        ami_id = global_config[region_name]['ami']
        response = client.describe_images(ImageIds=[ami_id])
        return response['Images'][0]['BlockDeviceMappings'][0]['Ebs']['VolumeSize']

    def deploy_instances(self):
        """
        Deploy instances at the requested cloud provider (CP) as configured by self.protocol_config
        :return:
        """
        regions = self.protocol_config['cloudProviders']['AWS']['regions']
        machine_type = self.protocol_config['cloudProviders']['AWS']['instanceType']
        if 'spotPrice' in self.protocol_config['cloudProviders']['AWS']:
            spot_request = True
            price_bids = self.protocol_config['cloudProviders']['AWS']['spotPrice']
        else:
            spot_request = False
        number_of_parties = self.protocol_config['cloudProviders']['AWS']['numOfParties']
        number_duplicated_servers = 0
        try:
            with open(f'{os.getcwd()}/GlobalConfigurations/awsRegions.json') as gc_file:
                global_config = json.load(gc_file, object_pairs_hook=OrderedDict)
        except EnvironmentError:
            print('Cannot open Global Configurations')

        os.makedirs('WebApp/DeploymentLogs', exist_ok=True)
        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Starting deploy servers for {self.protocol_name} protocol', file=output_file)
            if len(regions) > 1:
                number_of_instances = number_of_parties // len(regions)
                number_duplicated_servers = number_of_parties % len(regions)
            else:
                number_of_instances = number_of_parties

            date = datetime.utcnow()
            new_date = date + timedelta(hours=6)

            for idx in range(len(regions)):
                region_name = regions[idx][:-1]
                client = self.session.client('ec2', region_name=region_name)
                disk_size = self.get_ami_disk_size(region_name)

                number_of_instances_to_deploy = self.check_running_instances(region_name, machine_type)
                if idx < number_duplicated_servers:
                    number_of_instances_to_deploy = (number_of_instances - number_of_instances_to_deploy) + 1
                else:
                    number_of_instances_to_deploy = number_of_instances - number_of_instances_to_deploy

                if number_of_instances_to_deploy > 0:
                    if spot_request:
                        # check if price isn't too low
                        winning_bid_price = self.check_latest_price(machine_type, regions[idx])
                        request_bid = min(price_bids, winning_bid_price)
                        try:
                            response = client.request_spot_instances(
                                    DryRun=False,
                                    SpotPrice=str(request_bid),
                                    InstanceCount=number_of_instances_to_deploy,
                                    ValidUntil=new_date,
                                    LaunchSpecification=
                                    {
                                        'ImageId': global_config[regions[idx][:-1]]['ami'],
                                        'KeyName': global_config[regions[idx][:-1]]['key'],
                                        'SecurityGroups': [global_config[regions[idx][:-1]]['securityGroup']],
                                        'InstanceType': machine_type,
                                        'Placement':
                                            {
                                                'AvailabilityZone': regions[idx],
                                            },
                                    }
                            )
                            time.sleep(10)
                            spot_requests_ids = []
                            for request in response['SpotInstanceRequests']:
                                spot_requests_ids.append(request['SpotInstanceRequestId'])
                            instances_response = client.describe_spot_instance_requests(
                                Filters=[{'Name': 'spot-instance-request-id', 'Values': spot_requests_ids}])
                            instances_ids = []
                            for instance_response in instances_response['SpotInstanceRequests']:
                                instances_ids.append(instance_response['InstanceId'])
                            client.create_tags(Resources=instances_ids, Tags=[{
                                'Key': 'Name',
                                'Value': self.protocol_name
                            }])

                        except botocore.exceptions.ClientError as e:
                            print(e.response['Error']['Message'].upper())
                    else:
                        # check if vpc exists. use subnet id instead of security group if not exists
                        account = client.describe_account_attributes()
                        if 'VPC' in account['AccountAttributes'][0]['AttributeValues'][0]['AttributeValue']:
                            kwargs = {
                                'BlockDeviceMappings': [{
                                    'DeviceName': '/dev/sda1',
                                    'Ebs':
                                        {
                                            'DeleteOnTermination': True,
                                            'VolumeSize': disk_size
                                        }
                                },
                                    {
                                    'DeviceName': '/dev/sdf',
                                    'NoDevice': ''
                                    }
                                ],
                                'ImageId': global_config[region_name]["ami"],
                                'KeyName': global_config[region_name]["key"],
                                'MinCount': int(number_of_instances_to_deploy),
                                'MaxCount': int(number_of_instances_to_deploy),
                                'SecurityGroups': [global_config[region_name]["securityGroup"]],
                                'InstanceType': machine_type,
                                'Placement': {'AvailabilityZone': regions[idx]},
                                'TagSpecifications': [{
                                    'ResourceType': 'instance',
                                    'Tags': [{
                                        'Key': 'Name',
                                        'Value': self.protocol_name
                                    }]
                                }]
                            }
                        else:
                            kwargs = {
                                'BlockDeviceMappings': [{
                                    'DeviceName': '/dev/sda1',
                                    'Ebs':
                                        {
                                            'DeleteOnTermination': True,
                                            'VolumeSize': disk_size
                                        }
                                },
                                    {
                                        'DeviceName': '/dev/sdf',
                                        'NoDevice': ''
                                    }
                                ],
                                'ImageId': global_config[region_name]["ami"],
                                'KeyName': global_config[region_name]["key"],
                                'MinCount': int(number_of_instances_to_deploy),
                                'MaxCount': int(number_of_instances_to_deploy),
                                'SubnetId': [global_config[region_name]["subnetid"]],
                                'InstanceType': machine_type,
                                'Placement': {'AvailabilityZone': regions[idx]},
                                'TagSpecifications': [{
                                    'ResourceType': 'instance',
                                    'Tags': [{
                                        'Key': 'Name',
                                        'Value': self.protocol_name
                                    }]
                                }]
                            }
                        client.run_instances(**kwargs)
            print(f'waiting for the deploy to be finished', file=output_file)
            time.sleep(240)

            self.get_network_details()
            print(f'Deploy finished', file=output_file)

    def get_network_details(self, port_number=8000, file_name='parties.conf', new_format=False):
        """
        Creates party file for all the parties
        :type port_number int
        :param port_number: base port number
        :type file_name str
        :param file_name: the name of the file
        :type new_format bool
        :param new_format: using the new format or not
        """
        regions = self.protocol_config['cloudProviders']['AWS']['regions']
        is_spot_request = 'spotPrice' in self.protocol_config['cloudProviders']['AWS']
        coordinator_exists = 'coordinatorConfig' in self.protocol_config
        instance_type = self.protocol_config['cloudProviders']['AWS']['instanceType']

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'a+') as output_file:
            print(f'Fetching network topology for {self.protocol_name}', file=output_file)

        instances_ids = []
        public_ip_address = []
        private_ip_address = []

        # get the spot instances ids
        for idx in range(len(regions)):
            region_name = regions[idx][:-1]
            client = self.session.client('ec2', region_name=region_name)
            if is_spot_request:
                response = client.describe_instances(Filters=[{'Name': 'instance-lifecycle', 'Values': ['spot']},
                                                              {'Name': 'instance-type', 'Values': [instance_type]},
                                                              {'Name': 'tag:Name', 'Values': [self.protocol_name]}])

            else:
                response = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [self.protocol_name]}])

            # Extract instances ids
            for res_idx in range(len(response['Reservations'])):
                reservations_len = len(response['Reservations'][res_idx]['Instances'])
                for reserve_idx in range(reservations_len):
                    if response['Reservations'][res_idx]['Instances'][reserve_idx]['State']['Name'] == 'running':
                        if len(regions) == 1:
                            private_ip_address.append(response['Reservations'][res_idx]['Instances'][reserve_idx]
                                                      ['NetworkInterfaces'][0]['PrivateIpAddress'])
                        instances_ids.append(response['Reservations'][res_idx]['Instances'][reserve_idx]['InstanceId'])
                        public_ip_address.append(response['Reservations'][res_idx]
                                                 ['Instances'][reserve_idx]['PublicIpAddress'])

            # check if InstancesConfigurations dir exists
            if not os.path.isdir(f'{os.getcwd()}/InstancesConfigurations'):
                os.makedirs(f'{os.getcwd()}/InstancesConfigurations')

        if coordinator_exists == 'True':
            del private_ip_address[0]

        # rearrange the list that the ips from the same regions.json will not be followed
        if len(regions) > 1:
            shuffle(public_ip_address)
            self.create_parties_file(public_ip_address, port_number, file_name, new_format, len(regions))
        elif len(self.protocol_config['cloudProviders']) > 1:
            self.create_parties_file(public_ip_address, port_number, file_name, new_format, len(regions))
        else:
            self.create_parties_file(private_ip_address, port_number, file_name,  new_format, len(regions))

        # write public ips to file for fabric
        if len(self.protocol_config['cloudProviders']) > 1:
            mode = 'a+'
        else:
            mode = 'w+'
        try:
            with open('InstancesConfigurations/public_ips', mode) as public_ip_file:
                for public_idx in range(len(public_ip_address)):
                    public_ip_file.write(f'{public_ip_address[public_idx]}\n')
        except EnvironmentError:
            print('Cannot write public ips to file')

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'a+') as output_file:
            print(f'Network topology for {self.protocol_name} updated', file=output_file)

    def describe_instances(self, region_name, machines_name):
        """
        Retrieve all the machines associated to the protocol
        :type region_name str
        :param region_name: the regions that the instances are located
        :type machines_name str
        :param machines_name: the protocol name
        :return list of instances
        """
        client = self.session.client('ec2', region_name=region_name)
        is_spot_request = 'spotPrice' in self.protocol_config['cloudProviders']['AWS']
        if is_spot_request:
            response = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [machines_name]},
                                                          {'Name': 'instance-lifecycle', 'Values': ['spot']}])
        else:
            response = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [machines_name]}])
        instances = []

        for res_idx in range(len(response['Reservations'])):
            reservations_len = len(response['Reservations'][res_idx]['Instances'])
            for reserve_idx in range(reservations_len):
                instances.append(response['Reservations'][res_idx]['Instances'][reserve_idx]['InstanceId'])

        return instances

    def check_running_instances(self, region, machine_type):
        """
        Check how many instances are online
        :type region str
        :param region: the regions that the instances are located
        :type machine_type str
        :param machine_type: the type of the machines the protocol uses
        :return: number of online instances that associated to the protocol
        """
        ready_instances = 0

        client = self.session.client('ec2', region_name=region)
        response = client.describe_instances()

        for res_idx in range(len(response['Reservations'])):
            reservations_len = len(response['Reservations'][res_idx]['Instances'])
            for reserve_idx in range(reservations_len):
                if response['Reservations'][res_idx]['Instances'][reserve_idx]['State']['Name'] == 'running' and \
                        response['Reservations'][res_idx]['Instances'][reserve_idx]['Tags'][0]['Value'] == \
                        self.protocol_name and \
                        response['Reservations'][res_idx]['Instances'][reserve_idx]['InstanceType'] == machine_type:
                    ready_instances += 1

        return ready_instances

    def start_instances(self):
        """
        Turn on the instances
        """
        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Starting {self.protocol_name} instances', file=output_file)
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        for idx in range(len(regions)):
            region_name = regions[idx][:-1]
            instances = self.describe_instances(region_name, self.protocol_name)

            client = self.session.client('ec2', region_name=region_name)
            client.start_instances(InstanceIds=instances)
        time.sleep(20)
        self.get_network_details()

    def stop_instances(self):
        """
        Shut down the instances
        """
        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Shut down {self.protocol_name} instances', file=output_file)
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        for idx in range(len(regions)):
            region_name = regions[idx][:-1]
            instances = self.describe_instances(region_name, self.protocol_name)
            client = self.session.client('ec2', region_name=region_name)
            client.stop_instances(InstanceIds=instances)

    def reboot_instances(self):
        """
        Reboots the instances. Use this method if you want to reboot the instances.
        It will save you money instead of stop->start
        """
        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Rebooting {self.protocol_name} instances', file=output_file)
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        for idx in range(len(regions)):
            region_name = regions[idx][:-1]
            instances = self.describe_instances(region_name, self.protocol_name)
            client = self.session.client('ec2', region_name=region_name)
            client.reboot_instances(InstancesIds=instances)

    def change_instance_types(self):
        """
        Change the type of the instance the protocol uses.
        The new type should be specified at the protocol configuration file.
        """
        regions = self.protocol_config['cloudProviders']['AWS']['regions']
        instance_type = self.protocol_config['cloudProviders']['AWS']['instanceType']

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Changing {self.protocol_name} instances to {instance_type}', file=output_file)

        for idx in range(len(regions)):
            region_name = regions[idx][:-1]
            instances = self.describe_instances(region_name, self.protocol_name)
            client = self.session.client('ec2', region_name=region_name)
            client.stop_instances(InstanceIds=instances)
            waiter = client.get_waiter('instance_stopped')
            waiter.wait(InstanceIds=instances)

            for instance_idx in range(len(instances)):
                # Change the instance type
                client.modify_instance_attribute(InstanceId=instances[instance_idx],
                                                 Attribute='instanceType', Value=instance_type)

            # Start the instance
            client.start_instances(InstanceIds=instances)

        self.get_network_details()

    def terminate_instances(self):
        """
        Deletes the instances
        """

        with open(f'WebApp/DeploymentLogs/{self.protocol_name}.log', 'w+') as output_file:
            print(f'Terminate {self.protocol_name} instances ', file=output_file)
        regions = self.protocol_config['cloudProviders']['AWS']['regions']

        for idx in range(len(regions)):
            region_name = regions[idx][:-1]

            instances = self.describe_instances(region_name, self.protocol_name)

            client = self.session.client('ec2', region_name=region_name)
            client.terminate_instances(InstanceIds=instances)

    @staticmethod
    def copy_ami():
        """
        Copy the libscapi AMI to all other regions from the source region
        :return:
        """
        try:
            with open(f'{os.getcwd()}/GlobalConfigurations/awsRegions.json') as gc_file:
                data = json.load(gc_file, object_pairs_hook=OrderedDict)
        except EnvironmentError:
            print('Cannot open Global Configurations')

        source_region = input('enter source region:')
        regions_list = list(data.keys())
        regions_list.remove(source_region)

        for region in regions_list:
            client = self.session.client('ec2', region_name=region)
            response = client.copy_image(Description='libscapi image', Name='libscapi',
                                         SourceImageId=data[source_region]['ami'], SourceRegion=source_region)
            data[region]['ami'] = response['ImageId']

        try:
            with open('GlobalConfigurations/awsRegions.json', 'w') as regions_file:
                json.dump(data, regions_file)
        except EnvironmentError:
            print('Cannot write Global Configurations')
