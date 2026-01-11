#!/bin/bash

# NV-Ingest Library Mode Environment Setup Script
# This script exports all environment variables needed for running NV-Ingest
# with locally deployed NIM services via Docker Compose.
#
# Usage:
#   source scripts/setup_libmode_env.sh         # Set environment variables
#   source scripts/setup_libmode_env.sh --unset # Unset environment variables
#   # or
#   . scripts/setup_libmode_env.sh
#   . scripts/setup_libmode_env.sh --unset
#
# Note: This script should be sourced, not executed, so the environment
# variables persist in your current shell session.
#
# Prerequisites:
#   - Docker Compose services running (docker-compose up -d)
#   - All NIM services accessible via external port mappings

# Check for --unset parameter
if [ "$1" = "--unset" ]; then
    echo "🧹 Unsetting NV-Ingest Library Mode Environment Variables..."
    
    # =============================================================================
    # UNSET ALL ENVIRONMENT VARIABLES
    # =============================================================================
    
    # Core pipeline configuration
    unset INGEST_LOG_LEVEL
    unset INGEST_DISABLE_DYNAMIC_SCALING
    unset INGEST_DYNAMIC_MEMORY_THRESHOLD
    unset NGC_API_KEY
    
    # Message broker configuration
    unset MESSAGE_CLIENT_TYPE
    unset MESSAGE_CLIENT_HOST
    unset MESSAGE_CLIENT_PORT
    
    # NIM service endpoints
    unset YOLOX_GRPC_ENDPOINT
    unset YOLOX_HTTP_ENDPOINT
    unset YOLOX_INFER_PROTOCOL
    unset YOLOX_MODEL_NAME
    
    unset OCR_GRPC_ENDPOINT
    unset OCR_HTTP_ENDPOINT
    unset OCR_INFER_PROTOCOL
    unset OCR_MODEL_NAME
    
    unset YOLOX_TABLE_STRUCTURE_GRPC_ENDPOINT
    unset YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT
    unset YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL
    
    unset YOLOX_GRAPHIC_ELEMENTS_GRPC_ENDPOINT
    unset YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT
    unset YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL
    
    unset AUDIO_GRPC_ENDPOINT
    unset AUDIO_HTTP_ENDPOINT
    unset AUDIO_INFER_PROTOCOL
    unset AUDIO_FUNCTION_ID
    
    unset NEMORETRIEVER_PARSE_GRPC_ENDPOINT
    unset NEMORETRIEVER_PARSE_HTTP_ENDPOINT
    unset NEMORETRIEVER_PARSE_INFER_PROTOCOL
    unset NEMORETRIEVER_PARSE_MODEL_NAME
    
    unset VLM_CAPTION_ENDPOINT
    unset VLM_CAPTION_MODEL_NAME
    
    unset EMBEDDING_NIM_ENDPOINT
    unset EMBEDDING_NIM_MODEL_NAME
    
    # Telemetry and monitoring
    unset OTEL_EXPORTER_OTLP_ENDPOINT
    
    # Optional features
    unset INGEST_DISABLE_UDF_PROCESSING
    
    echo "✅ All NV-Ingest Library Mode environment variables have been unset."
    echo ""
    echo "💡 To set them again, run:"
    echo "   source scripts/setup_libmode_env.sh"
    echo ""
    
    return 0
fi

echo "🚀 Setting up NV-Ingest Library Mode Environment Variables..."

# =============================================================================
# CORE PIPELINE CONFIGURATION
# =============================================================================

export INGEST_LOG_LEVEL="DEBUG"

# Pipeline runtime settings
export INGEST_DISABLE_DYNAMIC_SCALING="true"
export INGEST_DYNAMIC_MEMORY_THRESHOLD="0.75"

# NGC API Key (required for NIM services)
# Set this to your actual NGC API key
export NGC_API_KEY="${NGC_API_KEY:-}"

# =============================================================================
# MESSAGE BROKER CONFIGURATION
# =============================================================================

# Service Broker configuration for libmode
# The libmode pipeline launches its own service broker internally (service_broker.enabled: true)
# and binds to 0.0.0.0:7671, making it accessible from external clients
export MESSAGE_CLIENT_TYPE="simple"
export MESSAGE_CLIENT_HOST="0.0.0.0"
export MESSAGE_CLIENT_PORT="7671"
export INGEST_SERVICE_BROKER_ENABLED="true"

# =============================================================================
# NIM SERVICE ENDPOINTS (Docker Compose External Port Mappings)
# =============================================================================

# YOLOX (Page Elements Detection) - External ports: 8000:8000, 8001:8001
export YOLOX_GRPC_ENDPOINT="localhost:8001"
export YOLOX_HTTP_ENDPOINT="http://localhost:8000/v1/infer"
export YOLOX_INFER_PROTOCOL="grpc"

# YOLOX Model Name Override (try common NIM model names)
# Uncomment one of these based on your NIM service's actual model name:
# export YOLOX_MODEL_NAME="yolox"                    # Default fallback
# export YOLOX_MODEL_NAME="yolox_ensemble"           # Preferred name
# export YOLOX_MODEL_NAME="nemoretriever-page-elements"  # NIM service name
# export YOLOX_MODEL_NAME="page-elements"            # Simplified name

# OCR (Optical Character Recognition) - External ports: 8009:8000, 8010:8001
export OCR_GRPC_ENDPOINT="localhost:8010"
export OCR_HTTP_ENDPOINT="http://localhost:8009/v1/infer"
export OCR_INFER_PROTOCOL="grpc"
export OCR_MODEL_NAME="scene_text_ensemble"

# Table Structure Detection - External ports: 8006:8000, 8007:8001
export YOLOX_TABLE_STRUCTURE_GRPC_ENDPOINT="localhost:8007"
export YOLOX_TABLE_STRUCTURE_HTTP_ENDPOINT="http://localhost:8006/v1/infer"
export YOLOX_TABLE_STRUCTURE_INFER_PROTOCOL="grpc"

# Graphic Elements Detection - External ports: 8003:8000, 8004:8001
export YOLOX_GRAPHIC_ELEMENTS_GRPC_ENDPOINT="localhost:8004"
export YOLOX_GRAPHIC_ELEMENTS_HTTP_ENDPOINT="http://localhost:8003/v1/infer"
export YOLOX_GRAPHIC_ELEMENTS_INFER_PROTOCOL="grpc"

# Audio Processing - External ports: 8021:50051, 8022:9000
export AUDIO_GRPC_ENDPOINT="localhost:8021"
export AUDIO_HTTP_ENDPOINT="http://localhost:8022/v1/infer"
export AUDIO_INFER_PROTOCOL="grpc"
export AUDIO_FUNCTION_ID=""

# NemoRetriever Parse - External ports: 8015:8000, 8016:8001
export NEMORETRIEVER_PARSE_GRPC_ENDPOINT="localhost:8016"
export NEMORETRIEVER_PARSE_HTTP_ENDPOINT="http://localhost:8015/v1/chat/completions"
export NEMORETRIEVER_PARSE_INFER_PROTOCOL="http"
export NEMORETRIEVER_PARSE_MODEL_NAME="nvidia/nemoretriever-parse"

# VLM Caption (Vision-Language Model) - External port: 8018:8000
export VLM_CAPTION_ENDPOINT="http://localhost:8018/v1/chat/completions"
export VLM_CAPTION_MODEL_NAME="nvidia/llama-3.1-nemotron-nano-vl-8b-v1"

# Text Embedding - External ports: 8012:8000, 8013:8001
export EMBEDDING_NIM_ENDPOINT="http://localhost:8012/v1"
export EMBEDDING_NIM_MODEL_NAME="nvidia/llama-3.2-nv-embedqa-1b-v2"

# =============================================================================
# TELEMETRY AND MONITORING
# =============================================================================

# OpenTelemetry endpoint for tracing - External port: 4317:4317
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# =============================================================================
# OPTIONAL FEATURES
# =============================================================================

# UDF (User Defined Functions) processing
# Set to "true" to disable UDF processing entirely
# export INGEST_DISABLE_UDF_PROCESSING="false"

# =============================================================================
# VALIDATION AND SUMMARY
# =============================================================================

echo "✅ Environment variables set for NV-Ingest Library Mode with locally deployed NIM services:"
echo ""
echo "📋 Core Configuration:"
echo "   INGEST_DISABLE_DYNAMIC_SCALING: $INGEST_DISABLE_DYNAMIC_SCALING"
echo "   INGEST_DYNAMIC_MEMORY_THRESHOLD: $INGEST_DYNAMIC_MEMORY_THRESHOLD"
echo "   NGC_API_KEY: ${NGC_API_KEY:+[SET]}${NGC_API_KEY:-[NOT SET - REQUIRED]}"
echo ""
echo "🔗 Message Broker:"
echo "   MESSAGE_CLIENT_TYPE: $MESSAGE_CLIENT_TYPE (Simple Broker - auto-launched by libmode)"
echo "   MESSAGE_CLIENT_HOST: $MESSAGE_CLIENT_HOST"
echo "   MESSAGE_CLIENT_PORT: $MESSAGE_CLIENT_PORT"
echo ""
echo "🤖 NIM Service Endpoints (Docker Compose External Ports):"
echo "   YOLOX (Page Elements): $YOLOX_GRPC_ENDPOINT (gRPC), $YOLOX_HTTP_ENDPOINT (HTTP)"
echo "   OCR: $OCR_GRPC_ENDPOINT (gRPC), $OCR_HTTP_ENDPOINT (HTTP)"
echo "   Table Structure: $YOLOX_TABLE_STRUCTURE_GRPC_ENDPOINT (gRPC)"
echo "   Graphic Elements: $YOLOX_GRAPHIC_ELEMENTS_GRPC_ENDPOINT (gRPC)"
echo "   Audio: $AUDIO_GRPC_ENDPOINT (gRPC)"
echo "   NemoRetriever Parse: $NEMORETRIEVER_PARSE_HTTP_ENDPOINT (HTTP)"
echo "   VLM Caption: $VLM_CAPTION_ENDPOINT"
echo "   Text Embedding: $EMBEDDING_NIM_ENDPOINT"
echo ""
echo "📊 Telemetry:"
echo "   OTEL_EXPORTER_OTLP_ENDPOINT: $OTEL_EXPORTER_OTLP_ENDPOINT"
echo ""

# Validation warnings
if [ -z "$NGC_API_KEY" ]; then
    echo "⚠️  WARNING: NGC_API_KEY is not set. This is required for NIM services."
    echo "   Set it with: export NGC_API_KEY='your-api-key-here'"
    echo ""
fi

echo "🎯 Ready to run NV-Ingest in library mode!"
echo ""
echo "💡 Next steps:"
echo "   1. Start Docker Compose NIM services: docker-compose up -d"
echo "   2. Wait for all NIM services to be ready (check docker-compose logs)"
echo "   3. Run your NV-Ingest libmode service (service broker auto-launches):"
echo "      python examples/launch_libmode_service.py"
echo "   4. In another terminal, submit jobs using the ingestor:"
echo "      python examples/launch_libmode_and_run_ingestor.py"
echo ""
echo "🔧 Port mappings (Docker external:internal):"
echo "   Redis: 6379:6379"
echo "   Page Elements: 8000:8000 (HTTP), 8001:8001 (gRPC)"
echo "   Graphic Elements: 8003:8000 (HTTP), 8004:8001 (gRPC)"
echo "   Table Structure: 8006:8000 (HTTP), 8007:8001 (gRPC)"
echo "   OCR: 8009:8000 (HTTP), 8010:8001 (gRPC)"
echo "   Embedding: 8012:8000 (HTTP), 8013:8001 (gRPC)"
echo "   NemoRetriever Parse: 8015:8000 (HTTP), 8016:8001 (gRPC)"
echo "   VLM: 8018:8000 (HTTP)"
echo "   Audio: 8021:50051 (gRPC), 8022:9000 (HTTP)"
echo ""
