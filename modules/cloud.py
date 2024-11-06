import boto3
import json
import base64
from botocore.exceptions import ClientError
from io import StringIO
import os
from .logger import logger

def get_aws_credentials():
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region_name = "us-east-1"

    session_params = {
    'region_name': region_name
    }

    if aws_access_key_id and aws_secret_access_key:
        logger.info("get_aws_credentials(): using .env credentials")
        session_params['aws_access_key_id'] = aws_access_key_id
        session_params['aws_secret_access_key'] = aws_secret_access_key
    else:
        logger.info("get_aws_credentials(): No environment variables for credentials found, assuming IAM role")
        logger.info("session params:", session_params)
    return boto3.Session(**session_params)

def get_secret():
    secret_name = os.getenv('AWS_SECRET_NAME')
    if not secret_name:
        logger.info("get_secret(): AWS_SECRET_NAME environment variable is not set, returning None secret_name")
        return None
    
    session = get_aws_credentials()
    client = session.client('secretsmanager')
    logger.info("get_secret(): got session:", session)

    try:
        # Retrieve the secret
        response = client.get_secret_value(SecretId=secret_name)

        # Decrypts secret using the associated KMS CMK if the secret is encrypted.
        if 'SecretString' in response:
            secret = response['SecretString']
        else:
            secret = base64.b64decode(response['SecretBinary'])

        # Convert the secret string to a dictionary
        secret_dict = json.loads(secret)
        return secret_dict

    except ClientError as e:
        # Handle the exception
        logger.error(f"Error retrieving secret: {e}")
        return None

def read_json_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')

    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        json_data = response['Body'].read().decode('utf-8')
        data = json.loads(json_data)
        
        return data

    except Exception as e:
        logger.error(f"Error reading JSON file from S3: {e}")
        return None

def write_csv_to_s3(dataframe, bucket_name, s3_file_path, aws_access_key_id=None, aws_secret_access_key=None):
    """
    :param s3_file_path: Path in the S3 bucket where the CSV will be stored (e.g., 'folder/file.csv')
    :param aws_access_key_id: AWS access key ID (optional)
    :param aws_secret_access_key: AWS secret access key (optional)
    """
    # Create a CSV buffer
    csv_buffer = StringIO()
    dataframe.to_csv(csv_buffer, index=False)

    # Create S3 client
    s3_client = boto3.client('s3', 
                              aws_access_key_id=aws_access_key_id, 
                              aws_secret_access_key=aws_secret_access_key)
    
    # Write the CSV buffer to S3
    s3_client.put_object(Bucket=bucket_name, Key=s3_file_path, Body=csv_buffer.getvalue())

def shutdown_instance():
    # Fetch instance ID using IMDSv2 if required
    try:
        token = os.popen("curl -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600'").read().strip()
        instance_id = os.popen(f"curl -H 'X-aws-ec2-metadata-token: {token}' http://169.254.169.254/latest/meta-data/instance-id").read().strip()
    except Exception as e:
        logger.error(f"Error fetching instance ID: {e}")
        return

    if not instance_id:
        logger.error("Instance ID is empty or malformed")
        return

    logger.info(f"Shutting down EC2 instance {instance_id}...")
    ec2_client = boto3.client('ec2')
    ec2_client.terminate_instances(InstanceIds=[instance_id])
