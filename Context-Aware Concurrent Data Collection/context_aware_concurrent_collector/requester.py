import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import core.aws_client as aws_client

if __name__ == "__main__":
    print(aws_client.AWSLambdaClient())
    