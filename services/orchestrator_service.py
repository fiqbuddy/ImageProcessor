"""
Orchestrator Service - Coordinates the entire image processing pipeline
Calls: Resize → Filter → Watermark → Format in sequence
NOW WITH LOAD BALANCING: Distributes requests across multiple service instances
Now uses XML-RPC instead of gRPC
"""
import sys
import os

# Fix Windows console encoding (simplified)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("🚀 Orchestrator Service starting...", flush=True)

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy, Binary
import sys
import os
import uuid
import time

# Fix Windows console encoding (simplified)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class OrchestratorService:
    def __init__(self, resize_hosts, filter_hosts, watermark_hosts, format_hosts):
        # Parse comma-separated hosts
        self.resize_hosts = [h.strip() for h in resize_hosts.split(',')]
        self.filter_hosts = [h.strip() for h in filter_hosts.split(',')]
        self.watermark_hosts = [h.strip() for h in watermark_hosts.split(',')]
        self.format_hosts = [h.strip() for h in format_hosts.split(',')]
        
        # Round-robin counters
        self.resize_idx = 0
        self.filter_idx = 0
        self.watermark_idx = 0
        self.format_idx = 0
        
        print(f"📊 Load Balancing Configuration:")
        print(f"   Resize instances:    {len(self.resize_hosts)} - {self.resize_hosts}")
        print(f"   Filter instances:    {len(self.filter_hosts)} - {self.filter_hosts}")
        print(f"   Watermark instances: {len(self.watermark_hosts)} - {self.watermark_hosts}")
        print(f"   Format instances:    {len(self.format_hosts)} - {self.format_hosts}")

    def _get_next_host(self, service_type):
        """Get next host using round-robin"""
        if service_type == 'resize':
            host = self.resize_hosts[self.resize_idx]
            self.resize_idx = (self.resize_idx + 1) % len(self.resize_hosts)
            return host
        elif service_type == 'filter':
            host = self.filter_hosts[self.filter_idx]
            self.filter_idx = (self.filter_idx + 1) % len(self.filter_hosts)
            return host
        elif service_type == 'watermark':
            host = self.watermark_hosts[self.watermark_idx]
            self.watermark_idx = (self.watermark_idx + 1) % len(self.watermark_hosts)
            return host
        elif service_type == 'format':
            host = self.format_hosts[self.format_idx]
            self.format_idx = (self.format_idx + 1) % len(self.format_hosts)
            return host
        return None

    def process_image(self, filename, image_data, options):
        """
        Process an image through the complete pipeline
        
        Args:
            filename: Name of the image file
            image_data: Binary image data (xmlrpc.client.Binary)
            options: Dictionary containing processing options:
                - target_width, target_height
                - filters: list of filter names
                - add_watermark, watermark_text, watermark_position
                - output_format, output_quality
        """
        process_id = str(uuid.uuid4())
        print(f"\n" + "="*70)
        print(f"[Orchestrator] Processing {filename} (process_id={process_id})")
        print(f"="*70 + "\n")
        
        start_total = time.time()
        current_image = image_data
        
        stats = {
            'original_size_bytes': len(image_data.data),
            'resize_time_ms': 0,
            'filter_time_ms': 0,
            'watermark_time_ms': 0,
            'format_time_ms': 0,
            'host_map': {}
        }
        
        try:
            # --- STAGE 1: RESIZE ---
            if options.get('target_width', 0) > 0 or options.get('target_height', 0) > 0:
                resize_host = self._get_next_host('resize')
                print(f"🖼  STAGE 1: Resizing image... (using {resize_host})")
                
                with ServerProxy(f'http://{resize_host}', allow_none=True) as proxy:
                    response = proxy.resize_image(
                        current_image,
                        process_id,
                        options.get('target_width', 0),
                        options.get('target_height', 0),
                        True  # maintain_aspect_ratio
                    )
                    
                    if not response['success']:
                        raise Exception(f"Resize failed: {response['message']}")
                    
                    current_image = response['resized_image']
                    stats['resize_time_ms'] = response['processing_time_ms']
                    stats['host_map']['Resize'] = resize_host
                    print(f"   ✅ Resized in {stats['resize_time_ms']}ms")
            else:
                print("⏭️  STAGE 1: Skipping resize")

            # --- STAGE 2: FILTERS ---
            filters = options.get('filters', [])
            if filters:
                print(f"🎨 STAGE 2: Applying {len(filters)} filter(s)...")
                filter_start = time.time()
                
                for i, filter_type in enumerate(filters):
                    filter_host = self._get_next_host('filter')
                    print(f"   [{i+1}/{len(filters)}] Applying {filter_type}... (using {filter_host})")
                    
                    with ServerProxy(f'http://{filter_host}', allow_none=True) as proxy:
                        response = proxy.apply_filter(
                            current_image,
                            process_id,
                            filter_type,
                            1.0  # intensity
                        )
                        
                        if not response['success']:
                            raise Exception(f"Filter {filter_type} failed: {response['message']}")
                        
                        current_image = response['filtered_image']
                        stats['host_map'][f"Filter-{i+1} ({filter_type})"] = filter_host
                
                stats['filter_time_ms'] = int((time.time() - filter_start) * 1000)
                print(f"   ✅ Filters applied in {stats['filter_time_ms']}ms")
            else:
                print("⏭️  STAGE 2: Skipping filters")

            # --- STAGE 3: WATERMARK ---
            if options.get('add_watermark', False):
                watermark_host = self._get_next_host('watermark')
                print(f"🏷️  STAGE 3: Adding watermark... (using {watermark_host})")
                
                with ServerProxy(f'http://{watermark_host}', allow_none=True) as proxy:
                    response = proxy.add_text_watermark(
                        current_image,
                        process_id,
                        options.get('watermark_text', ''),
                        options.get('watermark_position', 'bottom-right'),
                        30,  # font_size
                        "#FFFFFF",  # color
                        0.8  # opacity
                    )
                    
                    if not response['success']:
                        raise Exception(f"Watermark failed: {response['message']}")
                    
                    current_image = response['watermarked_image']
                    stats['watermark_time_ms'] = response['processing_time_ms']
                    stats['host_map']['Watermark'] = watermark_host
                    print(f"   ✅ Watermark added in {stats['watermark_time_ms']}ms")
            else:
                print("⏭️  STAGE 3: Skipping watermark")

            # --- STAGE 4: FORMAT/COMPRESSION ---
            format_host = self._get_next_host('format')
            print(f"📦 STAGE 4: Formatting/Compressing... (using {format_host})")
            
            with ServerProxy(f'http://{format_host}', allow_none=True) as proxy:
                # Default to PNG if not specified
                target_format = options.get('output_format', 'PNG')
                target_quality = options.get('output_quality', 90)
                if target_quality == 0:
                    target_quality = 90
                
                response = proxy.convert_format(
                    current_image,
                    process_id,
                    target_format,
                    target_quality
                )
                
                if not response['success']:
                    raise Exception(f"Format failed: {response['message']}")
                
                current_image = response['formatted_image']
                stats['format_time_ms'] = response['processing_time_ms']
                stats['host_map']['Format'] = format_host
                print(f"   ✅ Formatted in {stats['format_time_ms']}ms")

            # Finalize
            stats['total_time_ms'] = int((time.time() - start_total) * 1000)
            stats['processed_size_bytes'] = len(current_image.data)
            stats['host_map']['Orchestrator'] = "Device 5 (Master)"
            
            print(f"\n✅ Pipeline Complete! Total time: {stats['total_time_ms']}ms")
            
            return {
                'success': True,
                'message': "Processing completed successfully",
                'process_id': process_id,
                'processed_image': current_image,
                'stats': stats
            }

        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            return self._error_response(process_id, str(e))
    
    def _error_response(self, process_id, message):
        """Helper to create error response"""
        return {
            'success': False,
            'message': message,
            'process_id': process_id,
            'processed_image': Binary(b''),
            'stats': {}
        }
    
    def get_processing_status(self, process_id):
        """Get status of a processing job"""
        return {
            'process_id': process_id,
            'status': 'completed',
            'progress_percent': 100,
            'current_stage': 'done',
            'stats': {}
        }


def serve(port=50055):
    """Start the Orchestrator Service server"""
    
    # ------------------------------------------------------------------
    # 🔧 CONFIGURATION: Static IPs for all worker devices
    # ------------------------------------------------------------------
    DEFAULT_RESIZE_IP = '100.120.161.53'
    DEFAULT_FILTER_IP = '100.71.209.102'
    DEFAULT_WATERMARK_IP = '100.115.248.53'
    DEFAULT_FORMAT_IP = '100.71.185.127'
    # ------------------------------------------------------------------

    # Read service hosts from environment variables, OR use the default static IPs
    resize_hosts = os.getenv('RESIZE_SERVICE_HOSTS', f'{DEFAULT_RESIZE_IP}:50052')
    filter_hosts = os.getenv('FILTER_SERVICE_HOSTS', f'{DEFAULT_FILTER_IP}:50053')
    watermark_hosts = os.getenv('WATERMARK_SERVICE_HOSTS', f'{DEFAULT_WATERMARK_IP}:50054')
    format_hosts = os.getenv('FORMAT_SERVICE_HOSTS', f'{DEFAULT_FORMAT_IP}:50056')
    
    server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
    server.register_instance(
        OrchestratorService(resize_hosts, filter_hosts, watermark_hosts, format_hosts)
    )
    
    print(f"🎯 Orchestrator Service started on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    serve()
