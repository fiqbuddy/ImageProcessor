"""
Resize Service - Resizes images to specified dimensions
Computationally intensive: Uses Pillow for image manipulation
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import Binary
import sys
import os
import time
from io import BytesIO
from PIL import Image

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class ResizeService:
    def resize_image(self, image_data, image_id, target_width, target_height, maintain_aspect_ratio):
        """Resize an image to target dimensions"""
        print(f"[ResizeService] Processing image_id={image_id}, target={target_width}x{target_height}")
        
        start_time = time.time()
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            
            # Load image from bytes
            image = Image.open(BytesIO(image_bytes))
            original_size = image.size
            print(f"  Original size: {original_size[0]}x{original_size[1]}")
            
            # Calculate new dimensions
            if maintain_aspect_ratio:
                # Calculate aspect ratio
                aspect = original_size[0] / original_size[1]
                if target_width > 0 and target_height > 0:
                    # Use the dimension that results in smaller image
                    new_width = target_width
                    new_height = int(new_width / aspect)
                    if new_height > target_height:
                        new_height = target_height
                        new_width = int(new_height * aspect)
                elif target_width > 0:
                    new_width = target_width
                    new_height = int(new_width / aspect)
                else:
                    new_height = target_height
                    new_width = int(new_height * aspect)
            else:
                new_width = target_width if target_width > 0 else original_size[0]
                new_height = target_height if target_height > 0 else original_size[1]
            
            # Resize the image (use LANCZOS for high quality)
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            output_buffer = BytesIO()
            resized_image.save(output_buffer, format=image.format or 'PNG')
            resized_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"{'='*60}")
            print(f"✅ RESIZE COMPLETE")
            print(f"{'='*60}")
            print(f"   Image ID:      {image_id}")
            print(f"   Original:      {original_size[0]}x{original_size[1]}")
            print(f"   Resized to:    {new_width}x{new_height}")
            print(f"   Input size:    {len(image_bytes):,} bytes")
            print(f"   Output size:   {len(resized_bytes):,} bytes")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'message': f"Resized from {original_size[0]}x{original_size[1]} to {new_width}x{new_height}",
                'resized_image': Binary(resized_bytes),
                'new_width': new_width,
                'new_height': new_height,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return {
                'success': False,
                'message': f"Resize failed: {str(e)}",
                'resized_image': Binary(b''),
                'processing_time_ms': processing_time
            }
    
    def get_thumbnail(self, image_data, image_id, size):
        """Generate a square thumbnail"""
        print(f"[ResizeService] Creating thumbnail: size={size}")
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            image = Image.open(BytesIO(image_bytes))
            
            # Create square thumbnail
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Convert to bytes
            output_buffer = BytesIO()
            image.save(output_buffer, format='PNG')
            thumb_bytes = output_buffer.getvalue()
            
            return {
                'data': Binary(thumb_bytes),
                'width': image.width,
                'height': image.height,
                'format': 'PNG'
            }
            
        except Exception as e:
            print(f"  ❌ Thumbnail error: {str(e)}")
            return {
                'data': Binary(b''),
                'width': 0,
                'height': 0,
                'format': 'ERROR'
            }


def serve(port=50052):
    """Start the Resize Service server"""
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
    server.register_instance(ResizeService())
    print(f"🖼️  Resize Service started on port {port}\n")
    server.serve_forever()


if __name__ == '__main__':
    serve()
