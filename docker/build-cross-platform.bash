#!/bin/bash
# Cross-build the image for ARM v6 and v7
# NOTE this script automatically pushes the image to Docker hub so to run
#  successfully the $IMAGE_NAME below must be owned by the person running
#  the script 
# Based on https://www.docker.com/blog/faster-multi-platform-builds-dockerfile-cross-compilation-guide/

IMAGE_NAME=outlyernet/mi-temperature-2
THIS_DIR=$(dirname "$0")

TIMESTAMP=$(date --utc +%Y%m%d%H%M%S)

docker buildx create --use
docker buildx build --platform=linux/arm/v6,linux/arm/v7 \
    --push \
    -f "$THIS_DIR/Dockerfile.cross-platform" \
    -t $IMAGE_NAME:latest \
    -t $IMAGE_NAME:$TIMESTAMP \
    "$THIS_DIR/.."

