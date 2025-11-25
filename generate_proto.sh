#!/bin/bash
# Script to generate Python code from Protocol Buffers

# Create output directory for generated code
mkdir -p generated

# Generate Python code from proto file
python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ./protos/image_processing.proto

echo "✓ Protocol Buffer code generated successfully in ./generated/"
echo "✓ Generated files:"
echo "  - image_processing_pb2.py (message classes)"
echo "  - image_processing_pb2_grpc.py (service stubs and server classes)"
