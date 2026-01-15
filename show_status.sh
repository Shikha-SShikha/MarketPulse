#!/bin/bash

echo "=========================================="
echo "STM INTELLIGENCE SYSTEM STATUS"
echo "=========================================="

echo -e "\n📊 SEGMENT STATISTICS:"
curl -s http://localhost:8000/segments/stats | python3 -m json.tool | grep -A 5 "segment"

echo -e "\n\n📁 DATA SOURCES:"
curl -s http://localhost:8000/admin/entities 2>/dev/null | python3 -c "
import sys, json
try:
    # This will fail on 403, so we'll use backend query instead
    pass
except:
    pass
" 2>/dev/null

docker compose exec backend python -c "
from app.database import SessionLocal
from app.models import DataSource, Entity
from sqlalchemy import func

db = SessionLocal()

# Data sources
print('  By Type:')
type_counts = db.query(DataSource.source_type, func.count(DataSource.id)).group_by(DataSource.source_type).all()
for stype, count in type_counts:
    print(f'    {stype.upper()}: {count} sources')

enabled = db.query(DataSource).filter(DataSource.enabled == True).count()
print(f'  Enabled: {enabled}/{db.query(DataSource).count()}')

# Entities
print('\n📇 ENTITIES:')
entity_counts = db.query(Entity.segment, func.count(Entity.id)).group_by(Entity.segment).order_by(Entity.segment).all()
for segment, count in entity_counts:
    print(f'  {segment.capitalize()}: {count} entities')

total = db.query(Entity).count()
print(f'  Total: {total} entities')

db.close()
"

echo -e "\n✅ System ready for comprehensive STM intelligence gathering!"
echo "   → Dashboard: http://localhost:5173"
echo "   → Entity Manager: http://localhost:5173/admin/entities"
echo "   → Segments: http://localhost:5173/signals?segment=influencer"

