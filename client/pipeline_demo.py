"""
Image Processing Client - Demonstrates the complete pipeline with batch processing
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.client import ServerProxy, Binary
import sys
import os
import time
import shutil
from PIL import Image, ImageDraw
from io import BytesIO

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Filter and format constants (replacing protobuf enums)
FILTERS = {
    'GRAYSCALE': 'GRAYSCALE',
    'BLUR': 'BLUR',
    'SHARPEN': 'SHARPEN',
    'EDGE_DETECT': 'EDGE_DETECT',
    'SEPIA': 'SEPIA',
    'NEGATIVE': 'NEGATIVE',
    'BRIGHTNESS': 'BRIGHTNESS',
    'CONTRAST': 'CONTRAST'
}

FORMATS = {
    'PNG': 'PNG',
    'JPEG': 'JPEG',
    'WEBP': 'WEBP'
}


def create_sample_image(width=1920, height=1080):
    """Create a sample image for processing"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(128)
        b = int(255 * (1 - y / height))
        draw.rectangle([0, y, width, y + 1], fill=(r, g, b))
    
    # Shapes (scaled to image size)
    scale_x = width / 1920
    scale_y = height / 1080
    draw.rectangle([int(400*scale_x), int(300*scale_y), int(1500*scale_x), int(800*scale_y)], 
                   outline=(255, 255, 0), width=max(5, int(15*min(scale_x, scale_y))))
    draw.ellipse([int(600*scale_x), int(400*scale_y), int(1300*scale_x), int(700*scale_y)], 
                 fill=(0, 255, 255))
    
    # Text
    draw.text((width//2 - 100, height//2 - 30), "SAMPLE IMAGE", fill=(255, 255, 255))
    draw.text((width//2 - 120, height//2 + 30), "For XML-RPC Processing", fill=(255, 255, 255))
    
    return image


def process_image(proxy, image_data, filename, target_width=0, target_height=0, filters=None, watermark_text=None, output_format='PNG', output_quality=90):
    """Helper to send a request and print results"""
    if filters is None:
        filters = []
    
    # Create options dictionary
    options = {
        'target_width': target_width,
        'target_height': target_height,
        'filters': filters,
        'add_watermark': bool(watermark_text),
        'watermark_text': watermark_text or "",
        'watermark_position': "bottom-right",
        'output_format': output_format,
        'output_quality': output_quality
    }

    response = proxy.process_image(filename, Binary(image_data), options)
    
    if response['success']:
        # Save result
        result_img = Image.open(BytesIO(response['processed_image'].data))
        result_img.save(filename)
        
        print(f"✅ Success! Total: {response['stats']['total_time_ms']}ms | Saved: {filename}")
    else:
        print(f"❌ FAILED: {response['message']}")


def run_pipeline_demo():
    print("\n" + "="*80)
    print("🎨 IMAGE PROCESSING PIPELINE - Batch Demo")
    print("="*80 + "\n")
    
    # Clean output folder
    output_dir = "output"
    if os.path.exists(output_dir):
        print(f"🧹 Cleaning output folder...")
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"✅ Output folder ready\n")
    
    # Connect to Orchestrator
    print("🔌 Connecting to Orchestrator Service (port 50055)...")
    proxy = ServerProxy('http://localhost:50055', allow_none=True)
    
    # Batch processing configuration
    NUM_IMAGES = 30
    successful = 0
    failed = 0
    total_start_time = time.time()
    
    print("\n" + "="*80)
    print(f"🚀 BATCH PROCESSING: {NUM_IMAGES} Images")
    print("="*80)
    
    try:
        for i in range(1, NUM_IMAGES + 1):
            print(f"\n🎯 IMAGE {i}/{NUM_IMAGES}: ", end='', flush=True)
            
            # Create sample image (vary the size for diversity)
            sizes = [(1920, 1080), (1280, 720), (1600, 900), (2560, 1440)]
            width, height = sizes[i % len(sizes)]
            sample_image = create_sample_image(width, height)
            
            # Convert to bytes
            img_buffer = BytesIO()
            sample_image.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            # Vary the processing parameters
            filter_sets = [
                ['BLUR', 'SHARPEN'],
                ['SEPIA'],
                ['BRIGHTNESS', 'CONTRAST'],
                ['GRAYSCALE'],
            ]
            filters = filter_sets[i % len(filter_sets)]
            
            watermarks = [
                f"Image #{i}",
                f"Batch Processing",
                f"Distributed Pipeline",
                f"XML-RPC Demo"
            ]
            watermark = watermarks[i % len(watermarks)]
            
            try:
                process_image(
                    proxy,
                    img_bytes,
                    f"output/batch_{i:03d}.png",
                    target_width=1280,
                    target_height=720,
                    filters=filters,
                    watermark_text=watermark,
                    output_format='PNG',
                    output_quality=90
                )
                successful += 1
            except Exception as e:
                print(f"❌ Image {i} failed: {str(e)}")
                failed += 1
        
        # Summary
        total_time = time.time() - total_start_time
        print("\n" + "="*80)
        print("✨ BATCH PROCESSING COMPLETE!")
        print("="*80)
        print(f"   Total Images:      {NUM_IMAGES}")
        print(f"   Successful:        {successful}")
        print(f"   Failed:            {failed}")
        print(f"   Total Time:        {total_time:.2f}s")
        print(f"   Avg Time/Image:    {total_time/NUM_IMAGES:.2f}s")
        print(f"   Throughput:        {NUM_IMAGES/total_time:.2f} images/second")
        print("="*80)
        print(f"\n📂 Output: output/batch_001.png to output/batch_{NUM_IMAGES:03d}.png")
        print("💡 Check worker terminals to see distributed processing activity!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n🔧 Make sure all services are running!")


if __name__ == '__main__':
    run_pipeline_demo()
