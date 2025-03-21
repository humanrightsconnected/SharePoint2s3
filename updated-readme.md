# SharePoint2s3

A Python utility to recursively copy files from a SharePoint location to Amazon S3 while preserving the directory structure.

## Features

- Authenticates to SharePoint using username and password
- Recursively traverses folders in the specified SharePoint location
- Maintains the same directory structure when copying to S3
- Provides detailed logging and error handling
- Supports AWS profiles for authentication

## Requirements

- Python 3.6+
- SharePoint Online account credentials
- AWS credentials configured (either via environment variables, AWS profile, or IAM role)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SharePoint2s3.git
cd SharePoint2s3

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python sharepoint2s3.py --sharepoint-url "https://yourtenant.sharepoint.com/sites/yoursite" \
                       --sharepoint-username "user@yourtenant.onmicrosoft.com" \
                       --sharepoint-password "your-password" \
                       --sharepoint-folder "Shared Documents/your-folder" \
                       --s3-bucket "your-s3-bucket" \
                       --s3-prefix "optional/prefix" \
                       --aws-profile "optional-aws-profile" \
                       --verbose
```

### Required Parameters

- `--sharepoint-url`: The URL of your SharePoint site
- `--sharepoint-username`: SharePoint username (typically your email)
- `--sharepoint-password`: SharePoint password
- `--sharepoint-folder`: Relative path to the folder within the SharePoint site
- `--s3-bucket`: Name of the S3 bucket to copy files to

### Optional Parameters

- `--s3-prefix`: Prefix to add to S3 keys (e.g., "backup/2023/")
- `--aws-profile`: AWS profile name to use for authentication
- `--verbose`: Enable more detailed logging

## Security Considerations

- Avoid hardcoding SharePoint credentials in your scripts
- Consider using environment variables or a secrets manager for credentials
- For production use, implement more secure authentication methods

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
