import os
import subprocess
import sys
from datetime import datetime
import paramiko
from pathlib import Path
import uuid
import json
from dotenv import load_dotenv
import time

load_dotenv()

class RemarkableSync:
    def __init__(self, host=None, password=None):
        """
        Initialize reMarkable sync.
        host: IP address (reads from REMARKABLE_HOST env var if not provided)
        password: SSH password (reads from REMARKABLE_PASSWORD env var if not provided)
        """
        self.host = host or os.getenv('REMARKABLE_HOST', '10.11.99.1')
        self.password = password or os.getenv('REMARKABLE_PASSWORD')
        self.username = 'root'
        self.remote_path = '/home/root/.local/share/remarkable/xochitl/'
        self.ssh = None
        self.sftp = None
    
    def connect(self, retries=3, retry_delay=2):
        """Establish SSH connection with retry logic."""
        for attempt in range(retries):
            try:
                print(f"Connecting to {self.host}... (attempt {attempt + 1}/{retries})")
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(
                    self.host, 
                    username=self.username, 
                    password=self.password,
                    timeout=15,
                    banner_timeout=15,
                    auth_timeout=15
                )
                self.sftp = self.ssh.open_sftp()
                print("✓ Connected successfully")
                return True
            except Exception as e:
                print(f"✗ Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        
        print("\n✗ Could not connect to reMarkable")
        print("Possible reasons: device off, not on network, or wrong credentials")
        return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
    
    def create_folder(self, folder_name, parent_id=""):
        """Create a folder on reMarkable and return its UUID."""
        folder_id = str(uuid.uuid4())
        
        remote_metadata = f"{self.remote_path}{folder_id}.metadata"
        remote_content = f"{self.remote_path}{folder_id}.content"
        
        metadata = {
            "deleted": False,
            "lastModified": str(int(datetime.now().timestamp() * 1000)),
            "metadatamodified": False,
            "modified": False,
            "parent": parent_id,
            "pinned": False,
            "synced": False,
            "type": "CollectionType",
            "version": 1,
            "visibleName": folder_name
        }
        
        metadata_content = json.dumps(metadata)
        with self.sftp.open(remote_metadata, 'w') as f:
            f.write(metadata_content)
        
        content = {}
        content_str = json.dumps(content)
        with self.sftp.open(remote_content, 'w') as f:
            f.write(content_str)
        
        print(f"✓ Created folder: {folder_name}")
        return folder_id
    
    def find_folder(self, folder_name, parent_id=""):
        """Find a folder by name and return its UUID, or None if not found."""
        try:
            files = self.sftp.listdir(self.remote_path)
            metadata_files = [f for f in files if f.endswith('.metadata')]
            
            for metadata_file in metadata_files:
                try:
                    with self.sftp.open(f"{self.remote_path}{metadata_file}", 'r') as f:
                        metadata = json.load(f)
                        if (metadata.get('visibleName') == folder_name and 
                            metadata.get('type') == 'CollectionType' and
                            metadata.get('parent') == parent_id and
                            not metadata.get('deleted', False)):
                            return metadata_file.replace('.metadata', '')
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Error finding folder: {e}")
            return None
    
    def get_or_create_folder(self, folder_name, parent_id=""):
        """Get existing folder UUID or create new one."""
        folder_id = self.find_folder(folder_name, parent_id)
        if folder_id:
            print(f"✓ Found existing folder: {folder_name}")
            return folder_id
        else:
            return self.create_folder(folder_name, parent_id)
    
    def find_document(self, doc_name, parent_id=""):
        """Find a document by name in a folder and return its UUID."""
        try:
            files = self.sftp.listdir(self.remote_path)
            metadata_files = [f for f in files if f.endswith('.metadata')]
            
            for metadata_file in metadata_files:
                try:
                    with self.sftp.open(f"{self.remote_path}{metadata_file}", 'r') as f:
                        metadata = json.load(f)
                        if (metadata.get('visibleName') == doc_name and 
                            metadata.get('type') == 'DocumentType' and
                            metadata.get('parent') == parent_id and
                            not metadata.get('deleted', False)):
                            return metadata_file.replace('.metadata', '')
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Error finding document: {e}")
            return None
    
    def upload_pdf(self, local_pdf_path, parent_id="", update_existing=True):
        """
        Upload a PDF to reMarkable via SSH.
        
        update_existing: If True, updates existing file in-place (preserves annotations).
                        If False, creates new file (duplicates).
        """
        pdf_name = Path(local_pdf_path).stem
        
        doc_id = None
        if update_existing:
            doc_id = self.find_document(pdf_name, parent_id)
            if doc_id:
                print(f"Updating existing document: {pdf_name} (preserving annotations)")
        
        if not doc_id:
            doc_id = str(uuid.uuid4())
            print(f"Creating new document: {pdf_name}")
        
        try:
            remote_pdf = f"{self.remote_path}{doc_id}.pdf"
            remote_metadata = f"{self.remote_path}{doc_id}.metadata"
            remote_content = f"{self.remote_path}{doc_id}.content"
            
            self.sftp.put(local_pdf_path, remote_pdf)
            
            try:
                with self.sftp.open(remote_metadata, 'r') as f:
                    metadata = json.load(f)
                metadata['lastModified'] = str(int(datetime.now().timestamp() * 1000))
                metadata['modified'] = True
            except:
                metadata = {
                    "deleted": False,
                    "lastModified": str(int(datetime.now().timestamp() * 1000)),
                    "metadatamodified": False,
                    "modified": False,
                    "parent": parent_id,
                    "pinned": False,
                    "synced": False,
                    "type": "DocumentType",
                    "version": 1,
                    "visibleName": pdf_name
                }
            
            with self.sftp.open(remote_metadata, 'w') as f:
                f.write(json.dumps(metadata))
            
            try:
                with self.sftp.open(remote_content, 'r') as f:
                    content = json.load(f)
            except:
                content = {
                    "extraMetadata": {},
                    "fileType": "pdf",
                    "fontName": "",
                    "lastOpenedPage": 0,
                    "lineHeight": -1,
                    "margins": 100,
                    "orientation": "portrait",
                    "pageCount": 0,
                    "pages": [],
                    "textScale": 1,
                    "transform": {}
                }
            
            with self.sftp.open(remote_content, 'w') as f:
                f.write(json.dumps(content))
            
            print(f"✓ Uploaded {pdf_name}")
            return True
            
        except Exception as e:
            print(f"✗ Error uploading {pdf_name}: {e}")
            return False
    
    def upload_directory(self, directory_path, folder_name=None, update_existing=True, fail_on_error=False):
        """
        Upload PDFs in a directory to a folder.
        
        update_existing: If True, updates files in-place (preserves annotations).
                        If False, creates new files (duplicates).
        fail_on_error: If True, raises exception on connection failure.
                      If False, logs error and continues (for automated runs).
        """
        pdf_files = list(Path(directory_path).glob('*.pdf'))
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return False
        
        print(f"Found {len(pdf_files)} PDF files to upload")
        
        if not self.connect():
            if fail_on_error:
                raise ConnectionError("Could not connect to reMarkable")
            else:
                print("⚠ Sync skipped - device not reachable")
                return False
        
        try:
            if folder_name:
                parent_id = self.get_or_create_folder(folder_name)
            else:
                parent_id = ""
            
            for pdf_file in pdf_files:
                self.upload_pdf(str(pdf_file), parent_id=parent_id, update_existing=update_existing)
            
            print("\nRestarting reMarkable interface...")
            self.ssh.exec_command('systemctl restart xochitl')
            print(f"✓ Upload complete!")
            return True
            
        finally:
            self.disconnect()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Sync PDFs to reMarkable tablet')
    parser.add_argument('--path', help='PDF file or directory to upload')
    parser.add_argument('--folder', help='reMarkable folder name (e.g., "2026")')
    parser.add_argument('--host', help='reMarkable IP (reads from REMARKABLE_HOST env var if not provided)')
    parser.add_argument('--password', help='SSH password (reads from REMARKABLE_PASSWORD env var if not provided)')
    parser.add_argument('--new', action='store_true',
                       help='Create new files instead of updating (creates duplicates)')
    parser.add_argument('--fail-on-error', action='store_true',
                       help='Exit with error if sync fails (default: log and continue)')
    
    args = parser.parse_args()
    print(args.path)
    host = args.host or os.getenv('REMARKABLE_HOST')
    password = args.password or os.getenv('REMARKABLE_PASSWORD')
    
    if not password:
        print("Error: Password required. Set REMARKABLE_PASSWORD env var or use --password")
        sys.exit(1)
    
    if not host:
        print("Error: Host required. Set REMARKABLE_HOST env var or use --host")
        sys.exit(1)
    
    sync = RemarkableSync(host=host, password=password)
    
    update_existing = not args.new
    
    if os.path.isfile(args.path):
        if not sync.connect():
            if args.fail_on_error:
                sys.exit(1)
            else:
                print("⚠ Sync skipped - device not reachable")
                sys.exit(0)
        try:
            parent_id = ""
            if args.folder:
                parent_id = sync.get_or_create_folder(args.folder)
            sync.upload_pdf(args.path, parent_id=parent_id, update_existing=update_existing)
            sync.ssh.exec_command('systemctl restart xochitl')
        finally:
            sync.disconnect()
    elif os.path.isdir(args.path):
        folder_name = args.folder or Path(args.path).name
        success = sync.upload_directory(args.path, folder_name=folder_name, 
                                       update_existing=update_existing,
                                       fail_on_error=args.fail_on_error)
        if not success and args.fail_on_error:
            sys.exit(1)
    else:
        print(f"Error: {args.path} not found")
        sys.exit(1)


if __name__ == "__main__":
    main()