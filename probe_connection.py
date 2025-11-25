import grpc
import sys
import os

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc

def probe_service():
    # Get the IP from environment or ask user
    target_ip = os.environ.get('WORKER_IP')
    if not target_ip:
        target_ip = input("Enter Device 1 IP: ")
    
    print(f"Connecting to {target_ip}:50052...")
    
    channel = grpc.insecure_channel(f'{target_ip}:50052')
    stub = image_processing_pb2_grpc.ResizeServiceStub(channel)
    
    try:
        # Try to call the method
        print("Attempting to call ResizeImage...")
        response = stub.ResizeImage(image_processing_pb2.ResizeRequest(
            image_id="probe",
            image_data=b'123',
            target_width=100,
            target_height=100
        ))
        print("✅ SUCCESS! Method exists.")
    except grpc.RpcError as e:
        print(f"❌ ERROR: {e.code()}")
        print(f"Details: {e.details()}")
        
        if e.code() == grpc.StatusCode.UNIMPLEMENTED:
            print("\n🚨 DIAGNOSIS: The server is running, but it does NOT have the ResizeImage method.")
            print("This confirms the server is running OLD code (Movie Service?) or mismatched Proto files.")
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
            print("\n🚨 DIAGNOSIS: Cannot connect to server. Firewall or wrong IP.")

if __name__ == "__main__":
    probe_service()
