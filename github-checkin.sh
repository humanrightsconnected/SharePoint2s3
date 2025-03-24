#!/bin/bash
# Script to simulate GitHub repository setup and initial commit

# Initialize the repository
git init

# Add all files
git add sharepoint2s3.py
git add requirements.txt
git add README.md
git add .gitignore
mkdir -p .github/workflows
git add .github/workflows/python-tests.yml

# Create initial commit
git commit -m "Initial commit: SharePoint to S3 migration tool

- Add sharepoint2s3.py script for recursive file copying
- Add README with usage instructions
- Set up GitHub workflow for testing
- Include requirements.txt for dependencies"

# Create a license file
cat > LICENSE << 'EOL'
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOL

git add LICENSE
git commit -m "Add MIT License"

# Instructions for pushing to GitHub
echo "Repository initialized with initial commits."
echo ""
echo "To push to GitHub, create a new repository at https://github.com/new"
echo "Then run the following commands:"
echo ""
echo "  git remote add origin https://github.com/yourusername/SharePoint2s3.git"
echo "  git branch -M main"
echo "  git push -u origin main"
