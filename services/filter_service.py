"""
Filter Service - Applies various image filters (VERY CPU intensive)
Includes: Blur, Sharpen, Grayscale, Edge Detection, Sepia, etc.
Now uses XML-RPC instead of gRPC
"""
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import Binary
import sys
import os
import time
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Filter type constants (replacing protobuf enums)
FILTER_TYPES = {
    'GRAYSCALE': 'GRAYSCALE',
    'BLUR': 'BLUR',
    'SHARPEN': 'SHARPEN',
    'EDGE_DETECT': 'EDGE_DETECT',
    'SEPIA': 'SEPIA',
    'NEGATIVE': 'NEGATIVE',
    'BRIGHTNESS': 'BRIGHTNESS',
    'CONTRAST': 'CONTRAST'
}


class FilterService:
    
    def apply_filter_by_type(self, image, filter_type, intensity):
        """Apply the specified filter to the image"""
        
        if filter_type == 'GRAYSCALE':
            # Convert to grayscale
            gray = image.convert('L')
            if intensity < 1.0:
                # Blend with original based on intensity
                return Image.blend(image.convert('RGB'), gray.convert('RGB'), intensity)
            return gray.convert('RGB')
        
        elif filter_type == 'BLUR':
            # Apply Gaussian blur (CPU intensive)
            radius = max(1, int(20 * intensity))
            return image.filter(ImageFilter.GaussianBlur(radius))
        
        elif filter_type == 'SHARPEN':
            # Apply sharpening
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(1.0 + intensity * 2.0)
        
        elif filter_type == 'EDGE_DETECT':
            # Edge detection (very CPU intensive)
            edges = image.filter(ImageFilter.FIND_EDGES)
            if intensity < 1.0:
                return Image.blend(image, edges, intensity)
            return edges
        
        elif filter_type == 'SEPIA':
            # Sepia tone effect
            img_array = np.array(image.convert('RGB'))
            sepia_filter = np.array([[0.393, 0.769, 0.189],
                                    [0.349, 0.686, 0.168],
                                    [0.272, 0.534, 0.131]])
            sepia_img = img_array.dot(sepia_filter.T)
            sepia_img = np.clip(sepia_img, 0, 255).astype(np.uint8)
            result = Image.fromarray(sepia_img)
            if intensity < 1.0:
                return Image.blend(image, result, intensity)
            return result
        
        elif filter_type == 'NEGATIVE':
            # Invert colors
            img_array = np.array(image)
            inverted = 255 - img_array
            result = Image.fromarray(inverted)
            if intensity < 1.0:
                return Image.blend(image, result, intensity)
            return result
        
        elif filter_type == 'BRIGHTNESS':
            # Adjust brightness
            enhancer = ImageEnhance.Brightness(image)
            factor = 1.0 + (intensity - 0.5) * 2.0
            return enhancer.enhance(factor)
        
        elif filter_type == 'CONTRAST':
            # Adjust contrast
            enhancer = ImageEnhance.Contrast(image)
            factor = 1.0 + intensity * 2.0
            return enhancer.enhance(factor)
        
        else:
            return image
    
    def apply_filter(self, image_data, image_id, filter_type, intensity):
        """Apply a single filter to an image"""
        print(f"[FilterService] Applying {filter_type} (intensity={intensity:.2f}) to image_id={image_id}")
        
        start_time = time.time()
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Apply filter
            filtered_image = self.apply_filter_by_type(image, filter_type, intensity)
            
            # Convert back to bytes
            output_buffer = BytesIO()
            filtered_image.save(output_buffer, format='PNG')
            filtered_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            
            print(f"{'='*60}")
            print(f"✅ FILTER COMPLETE")
            print(f"{'='*60}")
            print(f"   Filter Type:   {filter_type}")
            print(f"   Intensity:     {intensity:.2f}")
            print(f"   Image ID:      {image_id}")
            print(f"   Input size:    {len(image_bytes):,} bytes")
            print(f"   Output size:   {len(filtered_bytes):,} bytes")
            print(f"   Processing:    {processing_time}ms")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'message': f"Applied {filter_type} filter",
                'filtered_image': Binary(filtered_bytes),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return {
                'success': False,
                'message': f"Filter failed: {str(e)}",
                'filtered_image': Binary(b''),
                'processing_time_ms': processing_time
            }
    
    def batch_filter(self, image_data, image_id, filters):
        """Apply multiple filters in sequence"""
        print(f"[FilterService] Batch processing {len(filters)} filters: {filters}")
        
        start_time = time.time()
        
        try:
            # Decode binary data from XML-RPC
            image_bytes = image_data.data
            
            # Load image
            image = Image.open(BytesIO(image_bytes))
            
            # Apply each filter sequentially
            for i, filter_type in enumerate(filters):
                print(f"  [{i+1}/{len(filters)}] Applying {filter_type}...")
                image = self.apply_filter_by_type(image, filter_type, 0.8)
            
            # Convert to bytes
            output_buffer = BytesIO()
            image.save(output_buffer, format='PNG')
            filtered_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ✅ Batch completed in {processing_time}ms")
            
            return {
                'success': True,
                'message': f"Applied {len(filters)} filters",
                'filtered_image': Binary(filtered_bytes),
                'total_processing_time_ms': processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Batch error: {str(e)}")
            return {
                'success': False,
                'message': f"Batch filter failed: {str(e)}",
                'filtered_image': Binary(b''),
                'total_processing_time_ms': processing_time
            }


def serve(port=50053):
    """Start the Filter Service server"""
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
    server.register_instance(FilterService())
    print(f"🎨 Filter Service started on port {port}\n")
    server.serve_forever()


if __name__ == '__main__':
    serve()
