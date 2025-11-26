"""
Test Resize Service - Quick demo of image resizing
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.client import ServerProxy, Binary
import sys
import os
import time
from PIL import Image
from io import BytesIO

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def create_test_image(width=1920, height=1080):
    """Create a colorful test image"""
    from PIL import ImageDraw
    
    # Create image with gradient
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Draw gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(255 * (1 - y / height))
        b = 128
        draw.rectangle([0, y, width, y + 1], fill=(r, g, b))
    
    # Draw some shapes
    draw.rectangle([width//4, height//4, 3*width//4, 3*height//4], 
                   outline=(255, 255, 0), width=10)
    draw.ellipse([width//3, height//3, 2*width//3, 2*height//3], 
                 fill=(255, 0, 255, 128))
    
    # Add text
    draw.text((width//2 - 100, height//2), "TEST IMAGE", fill=(255, 255, 255))
    
    return image


def test_resize_service():
    print("\n" + "="*70)
    print("🖼️  RESIZE SERVICE TEST")
    print("="*70 + "\n")
    
    # Create test image
    print("📸 Step 1: Creating test image (1920x1080)...")
    test_image = create_test_image(1920, 1080)
    
    # Convert to bytes
    img_buffer = BytesIO()
    test_image.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    
    print(f"   Original image size: {len(img_bytes):,} bytes\n")
    
    # Connect to Resize Service
    print("🔌 Step 2: Connecting to Resize Service (port 50052)...")
    proxy = ServerProxy('http://localhost:50052', allow_none=True)
    
    try:
        # Test 1: Resize to 800x600
        print("\n📏 Test 1: Resize to 800x600 (maintain aspect ratio)...")
        start = time.time()
        
        response = proxy.resize_image(
            Binary(img_bytes),
            "test_001",
            800,
            600,
            True  # maintain_aspect_ratio
        )
        
        if response['success']:
            print(f"   ✅ {response['message']}")
            print(f"   📊 New size: {response['new_width']}x{response['new_height']}")
            print(f"   ⏱️  Processing time: {response['processing_time_ms']}ms")
            print(f"   💾 Output size: {len(response['resized_image'].data):,} bytes")
            print(f"   📉 Compression: {(1 - len(response['resized_image'].data)/len(img_bytes))*100:.1f}%")
            
            # Save output
            resized_img = Image.open(BytesIO(response['resized_image'].data))
            resized_img.save("test_output_800x600.png")
            print(f"   💾 Saved as: test_output_800x600.png")
        else:
            print(f"   ❌ Failed: {response['message']}")
        
        # Test 2: Create thumbnail
        print("\n🖼️  Test 2: Creating 256x256 thumbnail...")
        thumb_response = proxy.get_thumbnail(
            Binary(img_bytes),
            "test_001",
            256
        )
        
        if thumb_response['data']:
            print(f"   ✅ Thumbnail created: {thumb_response['width']}x{thumb_response['height']}")
            print(f"   💾 Thumbnail size: {len(thumb_response['data'].data):,} bytes")
            
            # Save thumbnail
            thumb_img = Image.open(BytesIO(thumb_response['data'].data))
            thumb_img.save("test_thumbnail.png")
            print(f"   💾 Saved as: test_thumbnail.png")
        
        # Test 3: Multiple resizes to show CPU work
        print("\n⚡ Test 3: Batch processing (10 different sizes)...")
        sizes = [(1280, 720), (1024, 768), (800, 600), (640, 480), (320, 240),
                 (1600, 900), (1366, 768), (1440, 900), (1680, 1050), (1920, 1200)]
        
        total_start = time.time()
        for i, (w, h) in enumerate(sizes, 1):
            resp = proxy.resize_image(
                Binary(img_bytes),
                f"batch_{i}",
                w,
                h,
                True  # maintain_aspect_ratio
            )
            print(f"   [{i}/10] {w}x{h} -> {resp['processing_time_ms']}ms")
        
        total_time = (time.time() - total_start) * 1000
        print(f"\n   📊 Total processing time: {total_time:.0f}ms")
        print(f"   ⚡ Average per image: {total_time/10:.0f}ms")
        print(f"   🚀 Throughput: {10/(total_time/1000):.2f} images/second")
        
        print("\n" + "="*70)
        print("✅ All tests completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Make sure the Resize Service is running:")
        print("  python services/resize_service.py")
        print()


if __name__ == '__main__':
    test_resize_service()
