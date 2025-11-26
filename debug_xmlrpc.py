"""Simple test to debug XML-RPC communication"""
from xmlrpc.client import ServerProxy, Binary
from PIL import Image, ImageDraw
from io import BytesIO

# Create a small test image
image = Image.new('RGB', (100, 100), color='red')
img_buffer = BytesIO()
image.save(img_buffer, format='PNG')
img_bytes = img_buffer.getvalue()

print(f"Test image size: {len(img_bytes)} bytes")

# Connect to orchestrator
print("Connecting to orchestrator...")
try:
    proxy = ServerProxy('http://localhost:50055', allow_none=True)
    
    options = {
        'target_width': 50,
        'target_height': 50,
        'filters': [],
        'add_watermark': False,
        'watermark_text': "",
        'watermark_position': "bottom-right",
        'output_format': 'PNG',
        'output_quality': 90
    }
    
    print("Calling process_image...")
    response = proxy.process_image("test.png", Binary(img_bytes), options)
    
    print("\n=== RESPONSE ===")
    print(f"Type: {type(response)}")
    print(f"Keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
    print(f"Success: {response.get('success')}")
    print(f"Message: {response.get('message')}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
