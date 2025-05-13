import json
import requests
from requests.exceptions import RequestException
import json 

def lambda_handler(event, context):
    try:
        cookies = event['cookies']
        headers = event['headers']
        params = event['params']
        url = event['url']
        
        
        response = requests.get(url, 
                            params=params, 
                            cookies=cookies, 
                            headers=headers)
        
        # Check if response is successful
        if response.status_code == 200:
            return {
                'statusCode': 200,
                'body': response.text
            }
        else:
            # Handle non-200 responses
            return {
                'statusCode': response.status_code,
                'body': f"Error: Received status code {response.text}"
            }
    except RequestException as e:
        # Handle exceptions raised by requests.get
        return {'statusCode': 500, 'body': f"Error: {str(e)}"}