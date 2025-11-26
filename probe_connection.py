"""
Connection Probe - Test connectivity to XML-RPC services
"""
from xmlrpc.client import ServerProxy, Binary
import sys
import os

def probe_service():
    # Get the IP from environment or ask user
    target_ip = os.environ.get('WORKER_IP')
    if not target_ip:
        target_ip = input("Enter Device 1 IP: ")
    
    print(f"Connecting to {target_ip}:50052...")
    
    try:
        # Connect to resize service
        proxy = ServerProxy(f'http://{target_ip}:50052', allow_none=True)
        
        # Try to call the method with a simple test
        print("Attempting to call resize_image...")
        response = proxy.resize_image(
            Binary(b'test'),
            "probe",
            100,
            100,
            True
        )
        
        if response.get('success'):
            print("✅ SUCCESS! Service is running and responding.")
        else:
            print(f"⚠️  Service responded but with error: {response.get('message')}")
            
    except ConnectionRefusedError:
        print("❌ ERROR: Connection refused")
        print("\n🚨 DIAGNOSIS: Cannot connect to server. Check if service is running or firewall settings.")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        print(f"\n🚨 DIAGNOSIS: {str(e)}")

if __name__ == "__main__":
    probe_service()
