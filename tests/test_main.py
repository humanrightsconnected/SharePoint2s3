#!/usr/bin/env python3
"""
Unit tests for the main module in sharepoint2s3
"""

import unittest
from unittest import mock
import os
import sys
import argparse

# Add parent directory to the path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sharepoint2s3


class TestMain(unittest.TestCase):
    """Test cases for the main function in sharepoint2s3"""

    @mock.patch('sharepoint2s3.SharePointToS3')
    @mock.patch('sharepoint2s3.argparse.ArgumentParser.parse_args')
    def test_main_success(self, mock_parse_args, mock_sharepoint_to_s3):
        """Test the main function with successful execution"""
        # Mock command line arguments
        args = argparse.Namespace(
            sharepoint_url="https://test.sharepoint.com/sites/test",
            sharepoint_username="test@example.com",
            sharepoint_password="password",
            sharepoint_folder="Shared Documents",
            s3_bucket="test-bucket",
            s3_prefix="test-prefix",
            aws_profile=None,
            verbose=False
        )
        mock_parse_args.return_value = args
        
        # Mock SharePointToS3 instance
        mock_sp2s3_instance = mock_sharepoint_to_s3.return_value
        mock_sp2s3_instance.start_transfer.return_value = (10, 0)  # 10 successes, 0 errors
        
        # Call the main function
        with mock.patch('sys.exit') as mock_exit:
            sharepoint2s3.main()
            
            # Verify SharePointToS3 was instantiated with correct args
            mock_sharepoint_to_s3.assert_called_once_with(
                args.sharepoint_url,
                args.sharepoint_username,
                args.sharepoint_password,
                args.s3_bucket,
                args.s3_prefix,
                args.aws_profile
            )
            
            # Verify start_transfer was called
            mock_sp2s3_instance.start_transfer.assert_called_once_with(args.sharepoint_folder)
            
            # Verify exit was not called (no errors)
            mock_exit.assert_not_called()

    @mock.patch('sharepoint2s3.SharePointToS3')
    @mock.patch('sharepoint2s3.argparse.ArgumentParser.parse_args')
    def test_main_with_errors(self, mock_parse_args, mock_sharepoint_to_s3):
        """Test the main function with some errors during execution"""
        # Mock command line arguments
        args = argparse.Namespace(
            sharepoint_url="https://test.sharepoint.com/sites/test",
            sharepoint_username="test@example.com",
            sharepoint_password="password",
            sharepoint_folder="Shared Documents",
            s3_bucket="test-bucket",
            s3_prefix="test-prefix",
            aws_profile=None,
            verbose=False
        )
        mock_parse_args.return_value = args
        
        # Mock SharePointToS3 instance
        mock_sp2s3_instance = mock_sharepoint_to_s3.return_value
        mock_sp2s3_instance.start_transfer.return_value = (8, 2)  # 8 successes, 2 errors
        
        # Call the main function
        with mock.patch('sys.exit') as mock_exit:
            sharepoint2s3.main()
            
            # Verify exit was called with error code 1
            mock_exit.assert_called_once_with(1)

    @mock.patch('sharepoint2s3.SharePointToS3')
    @mock.patch('sharepoint2s3.argparse.ArgumentParser.parse_args')
    def test_main_exception(self, mock_parse_args, mock_sharepoint_to_s3):
        """Test the main function with an exception"""
        # Mock command line arguments
        args = argparse.Namespace(
            sharepoint_url="https://test.sharepoint.com/sites/test",
            sharepoint_username="test@example.com",
            sharepoint_password="password",
            sharepoint_folder="Shared Documents",
            s3_bucket="test-bucket",
            s3_prefix="test-prefix",
            aws_profile=None,
            verbose=False
        )
        mock_parse_args.return_value = args
        
        # Mock SharePointToS3 to raise an exception
        mock_sharepoint_to_s3.side_effect = Exception("Test exception")
        
        # Call the main function
        with mock.patch('sys.exit') as mock_exit:
            sharepoint2s3.main()
            
            # Verify exit was called with error code 1
            mock_exit.assert_called_once_with(1)

    @mock.patch('sharepoint2s3.logging.getLogger')
    @mock.patch('sharepoint2s3.argparse.ArgumentParser.parse_args')
    def test_verbose_logging(self, mock_parse_args, mock_get_logger):
        """Test that verbose flag sets appropriate logging level"""
        # Mock command line arguments with verbose=True
        args = argparse.Namespace(
            sharepoint_url="https://test.sharepoint.com/sites/test",
            sharepoint_username="test@example.com",
            sharepoint_password="password",
            sharepoint_folder="Shared Documents",
            s3_bucket="test-bucket",
            s3_prefix="test-prefix",
            aws_profile=None,
            verbose=True
        )
        mock_parse_args.return_value = args
        
        # Mock logger
        mock_logger = mock.MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Call the main function with the error handled
        with mock.patch('sharepoint2s3.SharePointToS3', side_effect=Exception("Test")):
            with mock.patch('sys.exit'):
                sharepoint2s3.main()
        
        # Verify logging level was set to DEBUG
        mock_logger.setLevel.assert_called_once_with(sharepoint2s3.logging.DEBUG)


if __name__ == '__main__':
    unittest.main()