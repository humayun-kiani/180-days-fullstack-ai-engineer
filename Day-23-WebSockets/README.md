# Day 23 — WebSockets: Real-Time Bidirectional Communication

> **Phase 2 — Web Development** | Week 4 | Day 23 of 180

---

## 📌 What I Learned Today

- Why HTTP polling is inefficient for real-time data
- How WebSocket handshake works (HTTP Upgrade → 101 Switching)
- Persistent bidirectional connection — either side can send anytime
- await websocket.accept() — complete the WebSocket handshake
- receive_text(), receive_json(), receive_bytes() — reading messages
- send_text(), send_json(), send_bytes() — sending messages
- WebSocketDisconnect exception — detect when client leaves
- JSON message protocol with type field for routing
- ConnectionManager pattern — track all active connections
- Broadcasting to all clients with for loop + exception handling
- Cleaning dead connections during broadcast
- Room pattern — project-based subscription groups
- join_room(), leave_room(), broadcast_to_room()
- defaultdict for automatic room creation
- ClientInfo class — metadata about each connection
- Presence system — see who's in the same room
- WebSocket authentication via query parameter token
- asyncio.wait_for() — timeout for auth messages
- WebSocket close codes: 1000 (normal), 4001 (auth failed)
- Message routing dispatch function (handle_message)
- Background task notification when task assigned to absent user
- StaticFiles middleware for serving HTML
- Response class HTMLResponse for serving the client page
- Heartbeat: ping/pong to detect stale connections
- Integration: WebSockets complement REST APIs, not replace them

## 🔨 Project Built

**Real-Time Task Board** — Full WebSocket application:

- TaskBoardManager with ClientInfo for rich connection metadata
- Project subscription rooms — subscribe to specific project updates
- Presence system — see who else is viewing the same project
- Real-time events: task_created, task_updated, task_completed
- Event broadcast to all project subscribers (not just the sender)
- Direct notification to task assignee if different from actor
- WebSocket auth via query token or first-message auth flow
- 8 message types: subscribe, complete, update, create, get_tasks,
  get_stats, ping, unsubscribe
- Beautiful dark-themed browser client with Kanban board layout
- Live message log showing all WebSocket traffic
- Live stats: total connections updated every 5 seconds
- Auto-refresh tasks when events received from other clients
- Popup notifications for user join/leave and completions

## 🚀 How to Run

```bash
cd Day-23-WebSockets
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# Open: http://localhost:8000
# Open two tabs, connect as different users, see real-time updates!

# Or test with wscat:
# wscat -c "ws://localhost:8000/ws?token=demo_token_humayun"
```

## 🧠 WebSocket vs HTTP

|            | HTTP                  | WebSocket           |
| ---------- | --------------------- | ------------------- |
| Connection | New per request       | Persistent          |
| Direction  | Client → Server       | Bidirectional       |
| Overhead   | Headers every request | Low after handshake |
| Real-time  | Polling required      | Native push         |
| Use case   | CRUD, files, auth     | Chat, live updates  |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
