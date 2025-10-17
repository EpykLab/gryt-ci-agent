#!/bin/bash
set -e

# Build script for gryt pipeline Docker image

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GRYT_SOURCE="/home/dhoenisch/code/gryt.dev"
IMAGE_NAME="${GRYT_DOCKER_IMAGE:-ghcr.io/epyklab/gryt/pipeline:latest}"

echo "Building gryt pipeline Docker image..."
echo "Image name: $IMAGE_NAME"
echo "Project root: $PROJECT_ROOT"
echo "Gryt source: $GRYT_SOURCE"

# Check if gryt source exists
if [ ! -d "$GRYT_SOURCE" ]; then
    echo "Error: gryt source directory not found at $GRYT_SOURCE"
    exit 1
fi

# Create a temporary build context
BUILD_CONTEXT=$(mktemp -d)
trap "rm -rf $BUILD_CONTEXT" EXIT

echo "Creating build context at $BUILD_CONTEXT..."

# Copy Dockerfile
cp "$SCRIPT_DIR/Dockerfile" "$BUILD_CONTEXT/"

# Copy gryt source
echo "Copying gryt source..."
cp -r "$GRYT_SOURCE" "$BUILD_CONTEXT/gryt.dev"

# Build the image
echo "Building Docker image..."
cd "$BUILD_CONTEXT"
docker build -t "$IMAGE_NAME" .

echo ""
echo "✓ Build complete!"
echo "Image: $IMAGE_NAME"
echo ""
echo "To test the image, run:"
echo "  docker run --rm $IMAGE_NAME gryt --help"
