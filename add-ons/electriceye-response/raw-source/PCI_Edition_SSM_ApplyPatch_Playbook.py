#This file is part of ElectricEye.
#SPDX-License-Identifier: Apache-2.0

#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at

#http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.
import boto3
import os

def lambda_handler(event, context):
    # boto3 clients
    sts = boto3.client('sts')
    securityhub = boto3.client('securityhub')
    # create env vars
    lambdaFunctionName = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    masterAccountId = sts.get_caller_identity()['Account']
    # parse ASFF
    securityHubEvent = (event['detail']['findings'])
    for findings in securityHubEvent:
        # parse finding ID
        findingId =str(findings['Id'])
        # parse Account from SecHub Finding
        findingOwner = str(findings['AwsAccountId'])
        for resources in findings['Resources']:
            resourceId = str(resources['Id'])
            ec2InstanceId = resourceId.replace('AWS::SSM::PatchCompliance:AWS::SSM::ManagedInstanceInventory/', '')
            if findingOwner != masterAccountId:
                memberAcct = sts.assume_role(RoleArn='arn:aws:iam::' + findingOwner + ':role/XA-ElectricEye-Response',RoleSessionName='x_acct_sechub')
                # retrieve creds from member account
                xAcctAccessKey = memberAcct['Credentials']['AccessKeyId']
                xAcctSecretKey = memberAcct['Credentials']['SecretAccessKey']
                xAcctSeshToken = memberAcct['Credentials']['SessionToken']
                # create service client using the assumed role credentials
                ssm = boto3.client('ssm',aws_access_key_id=xAcctAccessKey,aws_secret_access_key=xAcctSecretKey,aws_session_token=xAcctSeshToken)
                try:
                    # use ssm send command to run security patches
                    response = ssm.send_command(
                        InstanceIds=[ ec2InstanceId ],
                        DocumentName='AWS-RunPatchBaseline',
                        DocumentVersion='$LATEST',
                        TimeoutSeconds=360,
                        Comment='SSM Agent update launched by ElectricEye response playbook',
                        CloudWatchOutputConfig={ 'CloudWatchOutputEnabled': True }
                    )
                    print(response)
                    try:
                        response = securityhub.update_findings(
                            Filters={'Id': [{'Value': findingId,'Comparison': 'EQUALS'}]},
                            Note={'Text': 'Run Command was sent to invoke the AWS-RunPatchBaseline document for the instance and the finding was archived. Re-run Electric Eye or view the Run Command execution list in the account that the Command was sent to to ensure it was successfully executed.','UpdatedBy': lambdaFunctionName},
                            RecordState='ARCHIVED'
                        )
                        print(response)
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
            else:
                try:
                    ssm = boto3.client('ssm')
                    # use ssm send command to run security patches
                    response = ssm.send_command(
                        InstanceIds=[ ec2InstanceId ],
                        DocumentName='AWS-RunPatchBaseline',
                        DocumentVersion='$LATEST',
                        TimeoutSeconds=360,
                        Comment='SSM Agent update launched by ElectricEye response playbook',
                        CloudWatchOutputConfig={ 'CloudWatchOutputEnabled': True }
                    )
                    print(response)
                    try:
                        response = securityhub.update_findings(
                            Filters={'Id': [{'Value': findingId,'Comparison': 'EQUALS'}]},
                            Note={'Text': 'Run Command was sent to invoke the AWS-RunPatchBaseline document for the instance and the finding was archived. Re-run Electric Eye or view the Run Command execution list in the account that the Command was sent to to ensure it was successfully executed.','UpdatedBy': lambdaFunctionName},
                            RecordState='ARCHIVED'
                        )
                        print(response)
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)