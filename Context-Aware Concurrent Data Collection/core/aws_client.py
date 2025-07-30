import json
import logging
import os
import boto3
import botocore
from typing import Dict, Any, Optional
from .utils import retry_on_failure


class AWSLambdaClient:
    """AWS Lambda client management class"""
    
    def __init__(self, region_name: str = 'us-west-1'):
        self.region_name = region_name
        self.lambda_client = None
        self.setup_client()
    
    def setup_client(self):
        """Lambda client setup"""
        try:
            # Get AWS keys from environment variables, use hardcoded values if not available (not recommended for security)
            self.lambda_client = boto3.client(
                'lambda',
                region_name=self.region_name,
                # aws_access_key_id=AWS_ACCESS_KEY_ID,
                # aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
            logging.info(f"AWS Lambda client initialized for region: {self.region_name}")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Lambda client for {self.region_name}: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=5)
    def invoke_function(self, function_arn: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lambda function invocation"""
        try:
            if not self.lambda_client:
                logging.error("Lambda client not initialized")
                return None
            
            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            if response['StatusCode'] == 200:
                result = json.loads(response['Payload'].read())
                return result
            else:
                logging.error(f"Lambda function returned status: {response['StatusCode']}")
                return None
                
        except Exception as e:
            logging.error(f"Error invoking Lambda function {function_arn}: {str(e)}")
            return None
    
    def create_payload(self, url: str, params: Dict = None, cookies: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """Create payload for Lambda function invocation"""
        return {
            "url": url,
            "params": params or {},
            "cookies": cookies or {},
            "headers": headers or {}
        }
    
    def test_connection(self, function_arn: str) -> bool:
        """Test Lambda function connection"""
        try:
            test_payload = {"action": "test"}
            result = self.invoke_function(function_arn, test_payload)
            return result is not None
        except Exception as e:
            logging.error(f"Connection test failed for {function_arn}: {str(e)}")
            return False