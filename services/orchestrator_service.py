"""
Orchestrator Service - Coordinates the entire image processing pipeline
Calls: Resize → Filter → Watermark → Format in sequence
NOW WITH LOAD BALANCING: Distributes requests across multiple service instances
"""
print("🚀 Orchestrator Service starting...", flush=True)

import grpc
from concurrent import futures
import sys
import os
import uuid
import time
import random

# Fix Windows console encoding (simplified)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add generated code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'generated'))

import image_processing_pb2
import image_processing_pb2_grpc


class OrchestratorServiceServicer(image_processing_pb2_grpc.OrchestratorServiceServicer):
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

    def ProcessImage(self, request, context):
        process_id = str(uuid.uuid4())
        print(f"\n" + "="*70)
        print(f"[Orchestrator] Processing {request.filename} (process_id={process_id})")
        print(f"="*70 + "\n")
        
        start_total = time.time()
        current_image = request.image_data
        
        stats = image_processing_pb2.ProcessingStats()
        stats.original_size_bytes = len(current_image)
        
        try:
            # --- STAGE 1: RESIZE ---
            if request.options.target_width > 0 or request.options.target_height > 0:
                resize_host = self._get_next_host('resize')
                print(f"🖼  STAGE 1: Resizing image... (using {resize_host})")
                
                with grpc.insecure_channel(resize_host) as channel:
                    stub = image_processing_pb2_grpc.ResizeServiceStub(channel)
                    response = stub.ResizeImage(image_processing_pb2.ResizeRequest(
                        image_id=process_id,
                        image_data=current_image,
                        target_width=request.options.target_width,
                        target_height=request.options.target_height,
                        maintain_aspect_ratio=True
                    ))
                    
                    if not response.success:
                        raise Exception(f"Resize failed: {response.message}")
                    
                    current_image = response.resized_image
                    stats.resize_time_ms = response.processing_time_ms
                    print(f"   ✅ Resized in {stats.resize_time_ms}ms")
            else:
                print("⏭️  STAGE 1: Skipping resize")

            # --- STAGE 2: FILTERS ---
            if request.options.filters:
                print(f"🎨 STAGE 2: Applying {len(request.options.filters)} filter(s)...")
                filter_start = time.time()
                
                for i, filter_type in enumerate(request.options.filters):
                    filter_host = self._get_next_host('filter')
                    filter_name = image_processing_pb2.FilterType.Name(filter_type)
                    print(f"   [{i+1}/{len(request.options.filters)}] Applying {filter_name}... (using {filter_host})")
                    
                    with grpc.insecure_channel(filter_host) as channel:
                        stub = image_processing_pb2_grpc.FilterServiceStub(channel)
                        response = stub.ApplyFilter(image_processing_pb2.FilterRequest(
                            image_id=process_id,
                            image_data=current_image,
                            filter_type=filter_type,
                            intensity=1.0
                        ))
                        
                        if not response.success:
                            raise Exception(f"Filter {filter_name} failed: {response.message}")
                        
                        current_image = response.filtered_image
                
                stats.filter_time_ms = int((time.time() - filter_start) * 1000)
                print(f"   ✅ Filters applied in {stats.filter_time_ms}ms")
            else:
                print("⏭️  STAGE 2: Skipping filters")

            # --- STAGE 3: WATERMARK ---
            if request.options.add_watermark:
                watermark_host = self._get_next_host('watermark')
                print(f"🏷️  STAGE 3: Adding watermark... (using {watermark_host})")
                
                with grpc.insecure_channel(watermark_host) as channel:
                    stub = image_processing_pb2_grpc.WatermarkServiceStub(channel)
                    response = stub.AddTextWatermark(image_processing_pb2.TextWatermarkRequest(
                        image_id=process_id,
                        image_data=current_image,
                        text=request.options.watermark_text,
                        position=request.options.watermark_position or 'bottom-right',
                        font_size=30,
                        color="#FFFFFF",
                        opacity=0.8
                    ))
                    
                    if not response.success:
                        raise Exception(f"Watermark failed: {response.message}")
                    
                    current_image = response.watermarked_image
                    stats.watermark_time_ms = response.processing_time_ms
                    print(f"   ✅ Watermark added in {stats.watermark_time_ms}ms")
            else:
                print("⏭️  STAGE 3: Skipping watermark")

            # --- STAGE 4: FORMAT/COMPRESSION ---
            format_host = self._get_next_host('format')
            print(f"📦 STAGE 4: Formatting/Compressing... (using {format_host})")
            
            with grpc.insecure_channel(format_host) as channel:
                stub = image_processing_pb2_grpc.FormatServiceStub(channel)
                
                # Default to PNG if not specified
                target_format = request.options.output_format
                target_quality = request.options.output_quality
                if target_quality == 0: target_quality = 90
                
                response = stub.ConvertFormat(image_processing_pb2.FormatRequest(
                    image_id=process_id,
                    image_data=current_image,
                    format=target_format,
                    quality=target_quality
                ))
                
                if not response.success:
                    raise Exception(f"Format failed: {response.message}")
                
                current_image = response.formatted_image
                stats.format_time_ms = response.processing_time_ms
                print(f"   ✅ Formatted in {stats.format_time_ms}ms")

            # Finalize
            stats.total_time_ms = int((time.time() - start_total) * 1000)
            stats.processed_size_bytes = len(current_image)
            
            print(f"\n✅ Pipeline Complete! Total time: {stats.total_time_ms}ms")
            
            return image_processing_pb2.ProcessResponse(
                success=True,
                message="Processing completed successfully",
                process_id=process_id,
                processed_image=current_image,
                stats=stats
            )

        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            return self._error_response(process_id, str(e))
    
    def _error_response(self, process_id, message):
        """Helper to create error response"""
        return image_processing_pb2.ProcessResponse(
            success=False,
            message=message,
            process_id=process_id,
            processed_image=b'',
            stats=image_processing_pb2.ProcessingStats()
        )
    
    def GetProcessingStatus(self, request, context):
        """Get status of a processing job"""
        return image_processing_pb2.StatusResponse(
            process_id=request.process_id,
            status="completed",
            progress_percent=100,
            current_stage="done",
            stats=image_processing_pb2.ProcessingStats()
        )


def serve(port=50055):
    """Start the Orchestrator Service server"""
    
    # ------------------------------------------------------------------
    # 🔧 CONFIGURATION: Set your Worker Device IP here!
    # ------------------------------------------------------------------
    DEFAULT_WORKER_IP = '100.103.89.22'  # <--- CHANGE THIS TO DEVICE 1 IP
    # ------------------------------------------------------------------

    # Read service hosts from environment variables, OR use the default worker IP
    resize_hosts = os.getenv('RESIZE_SERVICE_HOSTS', f'{DEFAULT_WORKER_IP}:50052')
    filter_hosts = os.getenv('FILTER_SERVICE_HOSTS', f'{DEFAULT_WORKER_IP}:50053')
    watermark_hosts = os.getenv('WATERMARK_SERVICE_HOSTS', f'{DEFAULT_WORKER_IP}:50054')
    format_hosts = os.getenv('FORMAT_SERVICE_HOSTS', f'{DEFAULT_WORKER_IP}:50056')
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_processing_pb2_grpc.add_OrchestratorServiceServicer_to_server(
        OrchestratorServiceServicer(resize_hosts, filter_hosts, watermark_hosts, format_hosts), server
    )
    
    # Enable reflection
    SERVICE_NAMES = (
        image_processing_pb2.DESCRIPTOR.services_by_name['OrchestratorService'].full_name,
        grpc.reflection.SERVICE_NAME,
    )
    try:
        from grpc_reflection.v1alpha import reflection
        reflection.enable_server_reflection(SERVICE_NAMES, server)
    except ImportError:
        pass

    server.add_insecure_port(f'[::]:{port}')
    print(f"🎯 Orchestrator Service started on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
