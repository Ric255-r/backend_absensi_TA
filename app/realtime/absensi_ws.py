from fastapi import WebSocket

# Shared websocket connections for admin realtime updates.
absensi_connections: list[WebSocket] = []

# Ini dari User ke Admin
admin_to_user_conn = []

