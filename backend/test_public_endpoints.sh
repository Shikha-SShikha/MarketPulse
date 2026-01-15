#!/bin/bash

echo "==================================="
echo "ENTITY SEGMENTATION INTEGRATION TEST"
echo "==================================="

echo -e "\n1. Testing segment statistics..."
curl -s http://localhost:8000/segments/stats | python3 -m json.tool | head -30

echo -e "\n\n2. Testing signals with entities (customer segment)..."
curl -s 'http://localhost:8000/signals?segment=customer&limit=2' | python3 -m json.tool | grep -A 8 '"entities"'

echo -e "\n\n3. Testing signals with entities (influencer segment)..."
curl -s 'http://localhost:8000/signals?segment=influencer&limit=1' | python3 -m json.tool | head -50

echo -e "\n\n4. Verifying entity data structure..."
curl -s 'http://localhost:8000/signals?limit=1' | python3 -m json.tool | grep -A 12 '"entities"'

echo -e "\n\n✅ Integration test complete!"
