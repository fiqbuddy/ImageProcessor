"""
Format Service - Converts images to different formats and adjusts quality
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import Binary
import time
import os
import sys
from io import BytesIO
from PIL import Image

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Image format constants (replacing protobuf enums)
IMAGE_FORMATS = {
    'PNG': 'PNG',
    'JPEG': 'JPEG',
    'WEBP': 'WEBP'
}


class FormatService:
    def convert_format(self, image_data, image_id, format_type, quality):
        start_time = time.time()
        print(f"📦 Processing format request for image: {image_id}")
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            
            # Load image from bytes
            image = Image.open(BytesIO(image_bytes))
            
            # Determine output format
            output_format = 'PNG'  # Default
            if format_type == 'JPEG':
                output_format = 'JPEG'
                # JPEG doesn't support RGBA (transparency), convert to RGB
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
            elif format_type == 'WEBP':
                output_format = 'WEBP'
            
            # Save to bytes with specified quality
            output_buffer = BytesIO()
            
            # Quality handling
            if quality <= 0 or quality > 100:
                quality = 85  # Default quality
                
            print(f"   Converting to {output_format} with quality={quality}...")
            
            if output_format == 'PNG':
                # PNG is lossless, optimize=True helps size
                image.save(output_buffer, format='PNG', optimize=True)
            else:
                image.save(output_buffer, format=output_format, quality=quality)
                
            formatted_data = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"{'='*60}")
            print(f"✅ FORMAT COMPLETE")
            print(f"{'='*60}")
            print(f"   Output Format: {output_format}")
            print(f"   Quality:       {quality}%")
            print(f"   Image ID:      {image_id}")
            print(f"   Input size:    {len(image_bytes):,} bytes")
            print(f"   Output size:   {len(formatted_data):,} bytes")
            print(f"   Compression:   {((1 - len(formatted_data)/len(image_bytes)) * 100):.1f}%")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'message': "Format conversion successful",
                'formatted_image': Binary(formatted_data),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            print(f"❌ Error formatting image: {str(e)}")
            return {
                'success': False,
                'message': f"Format failed: {str(e)}",
                'formatted_image': Binary(b""),
                'processing_time_ms': 0
            }


def serve(port=50056):
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
    server.register_instance(FormatService())
    print(f"📦 Format Service started on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    # Allow port override via environment variable
    port = int(os.environ.get('PORT', 50056))
    serve(port)
