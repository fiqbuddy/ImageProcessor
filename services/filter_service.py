"""
Filter Service - Applies various image filters (VERY CPU intensive)
Includes: Blur, Sharpen, Grayscale, Edge Detection, Sepia, etc.
"""
import grpc
from concurrent import futures
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

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc


class FilterServiceServicer(image_processing_pb2_grpc.FilterServiceServicer):
    
    def apply_filter_by_type(self, image, filter_type, intensity):
        """Apply the specified filter to the image"""
        
        if filter_type == image_processing_pb2.GRAYSCALE:
            # Convert to grayscale
            gray = image.convert('L')
            if intensity < 1.0:
                # Blend with original based on intensity
                return Image.blend(image.convert('RGB'), gray.convert('RGB'), intensity)
            return gray.convert('RGB')
        
        elif filter_type == image_processing_pb2.BLUR:
            # Apply Gaussian blur (CPU intensive)
            radius = max(1, int(20 * intensity))
            return image.filter(ImageFilter.GaussianBlur(radius))
        
        elif filter_type == image_processing_pb2.SHARPEN:
            # Apply sharpening
            enhancer = ImageEnhance.Sharpness(image)
            return enhancer.enhance(1.0 + intensity * 2.0)
        
        elif filter_type == image_processing_pb2.EDGE_DETECT:
            # Edge detection (very CPU intensive)
            edges = image.filter(ImageFilter.FIND_EDGES)
            if intensity < 1.0:
                return Image.blend(image, edges, intensity)
            return edges
        
        elif filter_type == image_processing_pb2.SEPIA:
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
        
        elif filter_type == image_processing_pb2.NEGATIVE:
            # Invert colors
            img_array = np.array(image)
            inverted = 255 - img_array
            result = Image.fromarray(inverted)
            if intensity < 1.0:
                return Image.blend(image, result, intensity)
            return result
        
        elif filter_type == image_processing_pb2.BRIGHTNESS:
            # Adjust brightness
            enhancer = ImageEnhance.Brightness(image)
            factor = 1.0 + (intensity - 0.5) * 2.0
            return enhancer.enhance(factor)
        
        elif filter_type == image_processing_pb2.CONTRAST:
            # Adjust contrast
            enhancer = ImageEnhance.Contrast(image)
            factor = 1.0 + intensity * 2.0
            return enhancer.enhance(factor)
        
        else:
            return image
    
    def ApplyFilter(self, request, context):
        """Apply a single filter to an image"""
        filter_name = image_processing_pb2.FilterType.Name(request.filter_type)
        print(f"[FilterService] Applying {filter_name} (intensity={request.intensity:.2f}) to image_id={request.image_id}")
        
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(BytesIO(request.image_data))
            
            # Apply filter
            filtered_image = self.apply_filter_by_type(image, request.filter_type, request.intensity)
            
            # Convert back to bytes
            output_buffer = BytesIO()
            filtered_image.save(output_buffer, format='PNG')
            filtered_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ✅ {filter_name} completed in {processing_time}ms")
            
            return image_processing_pb2.FilterResponse(
                success=True,
                message=f"Applied {filter_name} filter",
                filtered_image=filtered_bytes,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Error: {str(e)}")
            return image_processing_pb2.FilterResponse(
                success=False,
                message=f"Filter failed: {str(e)}",
                filtered_image=b'',
                processing_time_ms=processing_time
            )
    
    def BatchFilter(self, request, context):
        """Apply multiple filters in sequence"""
        filter_names = [image_processing_pb2.FilterType.Name(f) for f in request.filters]
        print(f"[FilterService] Batch processing {len(request.filters)} filters: {filter_names}")
        
        start_time = time.time()
        
        try:
            # Load image
            image = Image.open(BytesIO(request.image_data))
            
            # Apply each filter sequentially
            for i, filter_type in enumerate(request.filters):
                filter_name = image_processing_pb2.FilterType.Name(filter_type)
                print(f"  [{i+1}/{len(request.filters)}] Applying {filter_name}...")
                image = self.apply_filter_by_type(image, filter_type, 0.8)
            
            # Convert to bytes
            output_buffer = BytesIO()
            image.save(output_buffer, format='PNG')
            filtered_bytes = output_buffer.getvalue()
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ✅ Batch completed in {processing_time}ms")
            
            return image_processing_pb2.BatchFilterResponse(
                success=True,
                message=f"Applied {len(request.filters)} filters",
                filtered_image=filtered_bytes,
                total_processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            print(f"  ❌ Batch error: {str(e)}")
            return image_processing_pb2.BatchFilterResponse(
                success=False,
                message=f"Batch filter failed: {str(e)}",
                filtered_image=b'',
                total_processing_time_ms=processing_time
            )


def serve(port=50053):
    """Start the Filter Service server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_FilterServiceServicer_to_server(
        FilterServiceServicer(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"🎨 Filter Service started on port {port}\n")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
