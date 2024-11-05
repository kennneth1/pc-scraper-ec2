import boto3
import json
import base64
from botocore.exceptions import ClientError
from io import StringIO

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

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
        print(f"Error retrieving secret: {e}")
        return None

def read_json_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')

    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        json_data = response['Body'].read().decode('utf-8')
        data = json.loads(json_data)
        
        return data

    except Exception as e:
        print(f"Error reading JSON file from S3: {e}")
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
