#!/bin/bash
set -e

cd /opt/cgraph/matrix

# Generate config using docker
docker run -it \
  -v "$(pwd)/config:/data" \
  -e SYNAPSE_SERVER_NAME=cgraph.org \
  -e SYNAPSE_REPORT_STATS=yes \
  matrixsynapse:latest \
  generate

echo "✅ Matrix config generated"
