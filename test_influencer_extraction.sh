#!/bin/bash

echo "=========================================="
echo "INFLUENCER ENTITY EXTRACTION TEST"
echo "=========================================="

echo -e "\n1. Verifying influencer entities in database..."
curl -s 'http://localhost:8000/segments/stats' | python3 -m json.tool | grep -A 4 "influencer"

echo -e "\n\n2. Testing influencer segment filtering..."
curl -s 'http://localhost:8000/signals?segment=influencer&limit=3' | python3 -m json.tool | grep -E '"topic"|"entity"|"name"|"segment"' | head -20

echo -e "\n\n3. Verifying entity extraction works for influencers..."
curl -s 'http://localhost:8000/signals?segment=influencer&limit=1' | python3 -m json.tool | grep -A 10 '"entities"'

echo -e "\n\n4. Checking all influencer entities..."
echo "Influencer signals by entity:"
curl -s 'http://localhost:8000/signals?segment=influencer&limit=100' | python3 -c "
import sys, json
data = json.load(sys.stdin)
entities = {}
for signal in data['signals']:
    if signal.get('entities'):
        for entity in signal['entities']:
            name = entity['name']
            entities[name] = entities.get(name, 0) + 1

for name, count in sorted(entities.items(), key=lambda x: -x[1]):
    print(f'  {name}: {count} signals')
"

echo -e "\n✅ Influencer extraction test complete!"
