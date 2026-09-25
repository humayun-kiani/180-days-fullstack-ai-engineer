 #!/bin/bash
# scripts/demo.sh
# Step-by-step demo script for TaskMind
# Run this while screen recording

set -e

BASE_URL="http://localhost:8000"
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "\n${CYAN}▶ $1${NC}"; sleep 1; }
show() { echo -e "${GREEN}$1${NC}"; }
note() { echo -e "${YELLOW}  → $1${NC}"; }

echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
echo -e "${CYAN}  TASKMIND DEMO SCRIPT${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"

step "1. Register a new user"
REGISTER=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@taskmind.dev","name":"Humayun Kiani","password":"demopassword123"}')
TOKEN=$(echo $REGISTER | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
show "  ✅ Registered. Token: ${TOKEN:0:40}..."
note "JWT contains: user_id, expiry. Signed with HS256."

AUTH="-H \"Authorization: Bearer $TOKEN\""

step "2. Create an urgent task"
TASK=$(curl -s -X POST "$BASE_URL/api/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"URGENT: Production database connection failure","priority":"urgent","description":"All API endpoints returning 503. DB connection pool exhausted."}')
TASK_ID=$(echo $TASK | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
show "  ✅ Task created: $TASK_ID"

step "3. AI analyzes the task"
ANALYSIS=$(curl -s -X POST "$BASE_URL/api/ai/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"URGENT: Production database connection failure"}')
echo $ANALYSIS | python3 -m json.tool
note "Claude reads the title and returns priority + reasoning + tags"

step "4. AI expands a vague task"
EXPAND=$(curl -s -X POST "$BASE_URL/api/ai/expand" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Add dark mode"}')
echo $EXPAND | python3 -m json.tool
note "Claude turns 3 words into a full engineering description"

step "5. AI breaks down a complex task"
BREAKDOWN=$(curl -s -X POST "$BASE_URL/api/ai/breakdown" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Build checkout page","description":"Full e-commerce checkout with payment"}')
echo $BREAKDOWN | python3 -m json.tool
note "Claude returns subtasks with time estimates"

step "6. Search tasks"
SEARCH=$(curl -s "$BASE_URL/api/search?q=production&sort_by=priority" \
  -H "Authorization: Bearer $TOKEN")
echo $SEARCH | python3 -m json.tool
note "Full-text ILIKE search + sorting in one query"

step "7. View statistics"
STATS=$(curl -s "$BASE_URL/api/stats" \
  -H "Authorization: Bearer $TOKEN")
echo $STATS | python3 -m json.tool
note "11 metrics computed in a single SQL aggregation query"

step "8. Export to CSV"
curl -s "$BASE_URL/api/tasks/export/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -o /tmp/tasks_demo.csv
show "  ✅ Exported to /tmp/tasks_demo.csv"
head -5 /tmp/tasks_demo.csv

step "9. Check profiling headers"
HEADERS=$(curl -sI "$BASE_URL/api/tasks" \
  -H "Authorization: Bearer $TOKEN" | grep -i "x-query\|x-db\|x-request" || true)
show "  Response headers:"
echo "$HEADERS"
note "Every response reports query count + DB time"

step "10. Weekly AI summary"
SUMMARY=$(curl -s "$BASE_URL/api/ai/weekly-summary" \
  -H "Authorization: Bearer $TOKEN")
echo $SUMMARY | python3 -m json.tool

echo -e "\n${CYAN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  DEMO COMPLETE ✅${NC}"
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo ""
echo "  Open the React UI: http://localhost"
echo "  API Docs:          http://localhost:8000/docs"
echo ""