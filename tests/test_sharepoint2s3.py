#!/usr/bin/env python3
"""
Unit tests for the SharePoint2s3 utility
"""

import unittest
from unittest import mock
import os
import sys
import io
from urllib.parse import urlparse

# Add parent directory to the path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sharepoint2s3 import SharePointToS3


class TestSharePointToS3(unittest.TestCase):
    """Test cases for the SharePointToS3 class"""

    @mock.patch('sharepoint2s3.AuthenticationContext')
    @mock.patch('sharepoint2s3.ClientContext')
    @mock.patch('sharepoint2s3.boto3.client')
    @mock.patch('sharepoint2s3.boto3.Session')
    def setUp(self, mock_session, mock_boto3_client, mock_client_context, mock_auth_context):
        """Set up test fixtures"""
        # Mock SharePoint context
        self.mock_auth_context_instance = mock_auth_context.return_value
        self.mock_client_context_instance = mock_client_context.return_value
        self.mock_web = mock.MagicMock()
        self.mock_client_context_instance.web = self.mock_web
        self.mock_web.properties = {'Title': 'Test Site'}
        
        # Mock S3 client
        self.mock_s3_client = mock_boto3_client.return_value
        
        # Create test instance
        self.sp2s3 = SharePointToS3(
            sharepoint_url="https://test.sharepoint.com/sites/test",
            username="test@example.com",
            password="password",
            s3_bucket="test-bucket",
            s3_prefix="test-prefix",
            aws_profile=None
        )
        
        # Reset mocks for actual tests
        mock_auth_context.reset_mock()
        mock_client_context.reset_mock()
        mock_boto3_client.reset_mock()
        mock_session.reset_mock()
    
    def test_init_with_aws_profile(self):
        """Test initialization with AWS profile"""
        with mock.patch('sharepoint2s3.AuthenticationContext') as mock_auth_context:
            with mock.patch('sharepoint2s3.ClientContext') as mock_client_context:
                with mock.patch('sharepoint2s3.boto3.Session') as mock_session:
                    # Setup mock
                    mock_client_context_instance = mock_client_context.return_value
                    mock_web = mock.MagicMock()
                    mock_client_context_instance.web = mock_web
                    mock_web.properties = {'Title': 'Test Site'}
                    mock_session_instance = mock_session.return_value
                    mock_s3_client = mock.MagicMock()
                    mock_session_instance.client.return_value = mock_s3_client
                    
                    # Create instance with AWS profile
                    sp2s3 = SharePointToS3(
                        sharepoint_url="https://test.sharepoint.com/sites/test",
                        username="test@example.com",
                        password="password",
                        s3_bucket="test-bucket",
                        s3_prefix="test-prefix",
                        aws_profile="test-profile"
                    )
                    
                    # Verify session was created with the profile
                    mock_session.assert_called_once_with(profile_name="test-profile")
                    mock_session_instance.client.assert_called_once_with('s3')

    def test_get_relative_path(self):
        """Test _get_relative_path method"""
        # Test with path that includes site URL
        result = self.sp2s3._get_relative_path("/sites/test/Shared Documents/folder/file.txt")
        self.assertEqual(result, "Shared Documents/folder/file.txt")
        
        # Test with path that doesn't include site URL
        result = self.sp2s3._get_relative_path("Shared Documents/folder/file.txt")
        self.assertEqual(result, "Shared Documents/folder/file.txt")
        
        # Test with leading slash but no site path
        result = self.sp2s3._get_relative_path("/Shared Documents/folder/file.txt")
        self.assertEqual(result, "Shared Documents/folder/file.txt")

    @mock.patch('sharepoint2s3.File.open_binary')
    def test_copy_folder(self, mock_open_binary):
        """Test copy_folder method"""
        # Mock file content
        mock_open_binary.return_value = b"test file content"
        
        # Mock folder structure
        mock_folder = mock.MagicMock()
        
        # Mock files in folder
        mock_file1 = mock.MagicMock()
        mock_file1.properties = {
            'ServerRelativeUrl': '/sites/test/Shared Documents/file1.txt',
            'Name': 'file1.txt'
        }
        mock_file2 = mock.MagicMock()
        mock_file2.properties = {
            'ServerRelativeUrl': '/sites/test/Shared Documents/file2.txt',
            'Name': 'file2.txt'
        }
        mock_folder.files = [mock_file1, mock_file2]
        
        # Mock subfolders - but return empty list to avoid recursion in tests
        # This will test the recursive call setup without actually recursing
        mock_subfolder = mock.MagicMock()
        mock_subfolder.properties = {
            'ServerRelativeUrl': '/sites/test/Shared Documents/subfolder',
            'Name': 'subfolder'
        }
        mock_folder.folders = [mock_subfolder]
        
        # For the first call, allow recursive lookup, but for subfolder return empty lists
        subfolder_instance = mock.MagicMock()
        subfolder_instance.files = []
        subfolder_instance.folders = []
        self.mock_client_context_instance.web.get_folder_by_server_relative_url.side_effect = [
            mock_folder,  # First call returns main folder
            subfolder_instance  # Second call returns subfolder with no files or folders
        ]
        
        # Call the method
        success_count, error_count = self.sp2s3.copy_folder("/sites/test/Shared Documents")
        
        # Verify results
        self.assertEqual(success_count, 2)  # Two files successfully copied
        self.assertEqual(error_count, 0)    # No errors
        
        # Verify the S3 client was called correctly for all files
        expected_calls = [
            mock.call(
                Bucket="test-bucket",
                Key="test-prefix/Shared Documents/file1.txt",
                Body=b"test file content"
            ),
            mock.call(
                Bucket="test-bucket",
                Key="test-prefix/Shared Documents/file2.txt",
                Body=b"test file content"
            )
        ]
        
        self.mock_s3_client.put_object.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(self.mock_s3_client.put_object.call_count, 2)
        
        # Verify recursive call
        self.mock_client_context_instance.web.get_folder_by_server_relative_url.assert_any_call(
            "/sites/test/Shared Documents/subfolder"
        )

    @mock.patch('sharepoint2s3.SharePointToS3.copy_folder')
    def test_start_transfer(self, mock_copy_folder):
        """Test start_transfer method"""
        # Mock copy_folder to return success
        mock_copy_folder.return_value = (5, 1)  # 5 successes, 1 error
        
        # Call the method
        success_count, error_count = self.sp2s3.start_transfer("Shared Documents")
        
        # Verify copy_folder was called with the correct path
        mock_copy_folder.assert_called_once_with("/sites/test/Shared Documents")
        
        # Verify results were passed through
        self.assertEqual(success_count, 5)
        self.assertEqual(error_count, 1)

    @mock.patch('sharepoint2s3.File.open_binary')
    def test_copy_folder_with_error(self, mock_open_binary):
        """Test copy_folder method with errors"""
        # Set up first file to succeed
        mock_open_binary.side_effect = [b"test file content", Exception("Test error")]
        
        # Mock folder structure
        mock_folder = mock.MagicMock()
        self.mock_client_context_instance.web.get_folder_by_server_relative_url.return_value = mock_folder
        
        # Mock files in folder
        mock_file1 = mock.MagicMock()
        mock_file1.properties = {
            'ServerRelativeUrl': '/sites/test/Shared Documents/file1.txt',
            'Name': 'file1.txt'
        }
        mock_file2 = mock.MagicMock()
        mock_file2.properties = {
            'ServerRelativeUrl': '/sites/test/Shared Documents/file2.txt',
            'Name': 'file2.txt'
        }
        mock_folder.files = [mock_file1, mock_file2]
        mock_folder.folders = []  # No subfolders
        
        # Call the method
        success_count, error_count = self.sp2s3.copy_folder("/sites/test/Shared Documents")
        
        # Verify results
        self.assertEqual(success_count, 1)  # One file successfully copied
        self.assertEqual(error_count, 1)    # One error
        
        # Verify the S3 client was called only for the first file
        self.mock_s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-prefix/Shared Documents/file1.txt",
            Body=b"test file content"
        )


if __name__ == '__main__':
    unittest.main()