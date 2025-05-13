import boto3
import botocore
import configparser
import json
import os
import time
import zipfile
from queue import Queue
from threading import Thread
import logging
import shutil
import tempfile
import sys
from threading import Lock

class LambdaUpdater:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.deployment_package = 'deployment-package.zip'
        self.update_lock = Lock()

    def update_deployment_package(self):
        # Read the updated zip file
        with open(os.path.join(self.current_dir, self.deployment_package), 'rb') as f:
            self.zipped_code = f.read()

    def update_lambda_functions(self, region, functionName):
        with self.update_lock:
            session = boto3.session.Session()
            client = session.client('lambda',
                                    aws_access_key_id="",
                                    aws_secret_access_key="",
                                    region_name=region)
            
            # Retry logic
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    self.update_deployment_package()
                    response = client.update_function_code(
                        FunctionName=functionName,
                        ZipFile=self.zipped_code
                    )
                    # print(region, functionName, "Update started", response)
                    # Wait for update to be successful
                    while True:
                        time.sleep(1)
                        response = client.get_function(FunctionName=functionName)
                        # print(region, functionName, response['Configuration']['LastUpdateStatus'])
                        if response['Configuration']['LastUpdateStatus'] == 'Successful':
                            print(region, functionName, "Update successful")
                            break
                    break  # Exit the retry loop if successful
                except Exception as e:
                    if e.response['Error']['Code'] == 'ResourceConflictException' and attempt < max_retries - 1:
                        logging.warning(f"Update in progress, retrying {functionName} (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(10)  # Wait before retrying
                    else:
                        logging.error(f"Failed to update {functionName}: {e}")
                        break
    
    def create_lambda_functions(self, region, start_index, end_index):
        session = boto3.session.Session()
        client = session.client('lambda',
                                aws_access_key_id="",
                                aws_secret_access_key="",
                                region_name=region)
        
        for i in range(start_index, end_index + 1):
            function_name = f'scraper_{i}'
            try:
                # Create the Lambda function
                response = client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.10',  # Specify the runtime for the Lambda function
                    Role='arn:aws:iam::{id}:role/LambdaExecutionRole',  # Replace with your IAM role ARN
                    Handler='lambda_function.lambda_handler',  # Main function entry point
                    Code={
                        'ZipFile': self.zipped_code
                    },
                    Timeout=120,  # Set function timeout as per your requirements
                    MemorySize=128,  # Set memory size (e.g., 128 MB)
                    Publish=True,
                    # Description=f'Lambda function {function_name}',
                    Architectures = ['arm64'],
                )
                print(f"Successfully created {function_name}")
            except botocore.exceptions.ClientError as e:
                logging.error(f"Failed to create function {function_name}: {e}")
            time.sleep(2)  # Optional: Add sleep to avoid overwhelming the API

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Load AWS Lambda function information
    with open(os.path.join(current_dir, '../aws_functions.json')) as f:
        aws = json.load(f)
    for region in aws:
        # print(region, aws[region])
        for function in aws[region]:
            print(region, function['arn'])
            LambdaUpdater().update_lambda_functions(region, function['arn'])