#!/bin/bash

# Initialize Production Database with Data Sources
# Usage: ./scripts/init_production.sh <API_URL> <CURATOR_TOKEN>

set -e

API_URL="${1:-}"
CURATOR_TOKEN="${2:-}"

if [ -z "$API_URL" ] || [ -z "$CURATOR_TOKEN" ]; then
  echo "Usage: $0 <API_URL> <CURATOR_TOKEN>"
  echo ""
  echo "Example:"
  echo "  $0 https://stm-intelligence-api.onrender.com your-production-token"
  echo ""
  echo "To get your CURATOR_TOKEN:"
  echo "  1. Go to Render Dashboard: https://dashboard.render.com"
  echo "  2. Select 'stm-intelligence-api' service"
  echo "  3. Go to Environment tab"
  echo "  4. Copy the CURATOR_TOKEN value"
  exit 1
fi

echo "🚀 Initializing production database..."
echo "📍 API URL: $API_URL"
echo ""

# Create data sources
echo "📡 Creating data sources..."

# 1. Nature News & Comment (RSS)
echo "  → Nature News & Comment"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nature News & Comment",
    "source_type": "rss",
    "url": "https://www.nature.com/nature/articles?type=news&type=comment.rss",
    "enabled": true,
    "default_confidence": "High",
    "config": {}
  }' || echo "  ⚠️  Already exists or failed"

# 2. Science News (RSS)
echo "  → Science News"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Science News",
    "source_type": "rss",
    "url": "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "enabled": true,
    "default_confidence": "High",
    "config": {}
  }' || echo "  ⚠️  Already exists or failed"

# 3. PLOS Blog (RSS)
echo "  → PLOS Blog"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PLOS Blog",
    "source_type": "rss",
    "url": "https://theplosblog.plos.org/feed/",
    "enabled": true,
    "default_confidence": "Medium",
    "config": {}
  }' || echo "  ⚠️  Already exists or failed"

# 4. Scholarly Kitchen (Web Scraper)
echo "  → Scholarly Kitchen"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scholarly Kitchen",
    "source_type": "web",
    "url": "https://scholarlykitchen.sspnet.org/",
    "enabled": true,
    "default_confidence": "High",
    "config": {
      "selectors": {
        "item": "article",
        "title": "h2 a, h3 a, .entry-title a",
        "link": "h2 a, h3 a, .entry-title a",
        "description": ".entry-content, .entry-summary"
      },
      "base_url": "https://scholarlykitchen.sspnet.org"
    }
  }' || echo "  ⚠️  Already exists or failed"

# 5. CSE Science Editor (RSS)
echo "  → CSE Science Editor"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CSE Science Editor",
    "source_type": "rss",
    "url": "https://www.csescienceeditor.org/feed/",
    "enabled": true,
    "default_confidence": "High",
    "config": {}
  }' || echo "  ⚠️  Already exists or failed"

# 6. STM Publishing News (RSS)
echo "  → STM Publishing News"
curl -X POST "$API_URL/admin/data-sources" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "STM Publishing News",
    "source_type": "rss",
    "url": "https://www.stm-publishing.com/feed/",
    "enabled": true,
    "default_confidence": "High",
    "config": {}
  }' || echo "  ⚠️  Already exists or failed"

echo ""
echo "✅ Data sources created!"
echo ""
echo "🔄 Triggering initial signal collection..."
curl -X POST "$API_URL/admin/collect-signals" \
  -H "Authorization: Bearer $CURATOR_TOKEN" \
  -H "Content-Type: application/json"

echo ""
echo ""
echo "✨ Production database initialized!"
echo ""
echo "🌐 Access your dashboard at:"
echo "   https://stm-intelligence-frontend.onrender.com"
echo ""
echo "🔑 Login with token: $CURATOR_TOKEN"
echo ""
