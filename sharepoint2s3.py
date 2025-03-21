#!/usr/bin/env python3
"""
SharePoint2s3 - A tool to recursively copy files from SharePoint to AWS S3
"""

import argparse
import logging
import os
import sys
from urllib.parse import urlparse
import boto3
import botocore
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('sharepoint2s3')


class SharePointToS3:
    """Main class to handle the transfer of files from SharePoint to S3"""

    def __init__(self, sharepoint_url, username, password, s3_bucket, s3_prefix="", aws_profile=None):
        """
        Initialize the SharePoint to S3 transfer tool

        Args:
            sharepoint_url (str): SharePoint site URL
            username (str): SharePoint username
            password (str): SharePoint password
            s3_bucket (str): S3 bucket name
            s3_prefix (str, optional): Prefix to add to S3 keys. Defaults to "".
            aws_profile (str, optional): AWS profile name. Defaults to None.
        """
        self.sharepoint_url = sharepoint_url
        self.username = username
        self.password = password
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix.rstrip('/') + '/' if s3_prefix else ""
        
        # Initialize SharePoint client
        try:
            auth_context = AuthenticationContext(sharepoint_url)
            auth_context.acquire_token_for_user(username, password)
            self.ctx = ClientContext(sharepoint_url, auth_context)
            self.ctx.load(self.ctx.web)
            self.ctx.execute_query()
            logger.info(f"Connected to SharePoint site: {self.ctx.web.properties['Title']}")
        except Exception as e:
            logger.error(f"Failed to authenticate with SharePoint: {str(e)}")
            raise
        
        # Initialize S3 client
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                self.s3_client = session.client('s3')
            else:
                self.s3_client = boto3.client('s3')
            
            # Verify bucket exists
            self.s3_client.head_bucket(Bucket=s3_bucket)
            logger.info(f"Connected to S3 bucket: {s3_bucket}")
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                logger.error(f"S3 bucket {s3_bucket} does not exist")
            elif error_code == '403':
                logger.error(f"No permission to access S3 bucket {s3_bucket}")
            else:
                logger.error(f"Error accessing S3 bucket: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to S3: {str(e)}")
            raise

    def _get_relative_path(self, sharepoint_path):
        """
        Convert SharePoint server relative path to a relative path
        
        Args:
            sharepoint_path (str): SharePoint server relative path
            
        Returns:
            str: Relative path
        """
        site_url = urlparse(self.sharepoint_url).path
        if sharepoint_path.startswith(site_url):
            return sharepoint_path[len(site_url):].lstrip('/')
        return sharepoint_path.lstrip('/')

    def copy_folder(self, folder_url):
        """
        Recursively copy a SharePoint folder to S3
        
        Args:
            folder_url (str): SharePoint folder URL
            
        Returns:
            tuple: (success_count, error_count)
        """
        success_count = 0
        error_count = 0
        
        try:
            # Get folder and its contents
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_url)
            self.ctx.load(folder)
            self.ctx.load(folder.files)
            self.ctx.load(folder.folders)
            self.ctx.execute_query()
            
            # Process all files in the folder
            for file_obj in folder.files:
                try:
                    relative_path = self._get_relative_path(file_obj.properties['ServerRelativeUrl'])
                    s3_key = f"{self.s3_prefix}{relative_path}"
                    
                    # Download file content from SharePoint
                    file_content = File.open_binary(self.ctx, file_obj.properties['ServerRelativeUrl'])
                    
                    # Upload to S3
                    logger.info(f"Copying file: {relative_path} -> s3://{self.s3_bucket}/{s3_key}")
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket,
                        Key=s3_key,
                        Body=file_content
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error copying file {file_obj.properties['ServerRelativeUrl']}: {str(e)}")
                    error_count += 1
            
            # Recursively process subfolders
            for subfolder in folder.folders:
                if subfolder.properties['Name'] not in ['.', '..', 'Forms']:  # Skip special folders
                    subfolder_url = subfolder.properties['ServerRelativeUrl']
                    sub_success, sub_error = self.copy_folder(subfolder_url)
                    success_count += sub_success
                    error_count += sub_error
                    
            return success_count, error_count
        
        except Exception as e:
            logger.error(f"Error processing folder {folder_url}: {str(e)}")
            return success_count, error_count + 1

    def start_transfer(self, relative_folder_path):
        """
        Start the transfer process from the given SharePoint folder
        
        Args:
            relative_folder_path (str): Relative path of the folder in SharePoint
            
        Returns:
            tuple: (success_count, error_count)
        """
        # Construct the server relative URL
        site_url = urlparse(self.sharepoint_url).path
        if not site_url.endswith('/'):
            site_url += '/'
        
        server_relative_url = site_url + relative_folder_path.lstrip('/')
        
        logger.info(f"Starting transfer from SharePoint folder: {server_relative_url}")
        logger.info(f"Target S3 location: s3://{self.s3_bucket}/{self.s3_prefix}")
        
        return self.copy_folder(server_relative_url)


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description='Copy files from SharePoint to S3')
    parser.add_argument('--sharepoint-url', required=True, help='SharePoint site URL')
    parser.add_argument('--sharepoint-username', required=True, help='SharePoint username')
    parser.add_argument('--sharepoint-password', required=True, help='SharePoint password')
    parser.add_argument('--sharepoint-folder', required=True, help='Relative path to the SharePoint folder')
    parser.add_argument('--s3-bucket', required=True, help='S3 bucket name')
    parser.add_argument('--s3-prefix', default='', help='Prefix to add to S3 keys')
    parser.add_argument('--aws-profile', help='AWS profile name')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Create and start the transfer
        transfer = SharePointToS3(
            args.sharepoint_url,
            args.sharepoint_username,
            args.sharepoint_password,
            args.s3_bucket,
            args.s3_prefix,
            args.aws_profile
        )
        
        success_count, error_count = transfer.start_transfer(args.sharepoint_folder)
        
        # Print summary
        logger.info(f"Transfer completed. Files copied successfully: {success_count}, Errors: {error_count}")
        
        if error_count > 0:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Transfer failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
