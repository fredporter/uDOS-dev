"""
uDOS WebSocket Streaming Service (v1.2.30)

Unified WebSocket streaming for all modular services.

Provides real-time streaming for:
- Command execution results
- Pager content updates
- Predictor suggestions
- Debug panel logs
- File picker navigation
- Menu state changes

Compatible with Flask-SocketIO backend.

Author: uDOS Development Team
Version: 1.2.30
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class StreamEvent(Enum):
    """WebSocket event types"""
    # Connection
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    
    # Commands
    COMMAND_START = "command_start"
    COMMAND_OUTPUT = "command_output"
    COMMAND_COMPLETE = "command_complete"
    COMMAND_ERROR = "command_error"
    
    # Pager
    PAGER_CONTENT = "pager_content"
    PAGER_SCROLL = "pager_scroll"
    PAGER_STATUS = "pager_status"
    
    # Predictor
    PREDICTOR_SUGGEST = "predictor_suggest"
    PREDICTOR_TOKENS = "predictor_tokens"
    
    # Debug Panel
    DEBUG_LOG = "debug_log"
    DEBUG_ERROR = "debug_error"
    DEBUG_STATS = "debug_stats"
    
    # File Picker
    FILES_LIST = "files_list"
    FILES_NAVIGATE = "files_navigate"
    FILES_SELECT = "files_select"
    
    # Menu
    MENU_OPEN = "menu_open"
    MENU_CLOSE = "menu_close"
    MENU_ACTION = "menu_action"
    
    # System
    SYSTEM_STATUS = "system_status"
    SYSTEM_UPDATE = "system_update"


@dataclass
class StreamMessage:
    """
    WebSocket message structure.
    
    Attributes:
        event: Event type
        data: Event payload
        correlation_id: Request correlation ID
        timestamp: ISO timestamp
        source: Originating service
    """
    event: StreamEvent
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "udos"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'event': self.event.value,
            'data': self.data,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp,
            'source': self.source,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class StreamSubscription:
    """
    Client subscription configuration.
    
    Tracks which events a client is subscribed to.
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.subscribed_events: Set[StreamEvent] = set()
        self.filters: Dict[str, Any] = {}
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
    
    def subscribe(self, events: List[StreamEvent] | str):
        """Subscribe to events"""
        if events == "all":
            self.subscribed_events = set(StreamEvent)
        elif isinstance(events, list):
            self.subscribed_events.update(events)
    
    def unsubscribe(self, events: List[StreamEvent] | str):
        """Unsubscribe from events"""
        if events == "all":
            self.subscribed_events.clear()
        elif isinstance(events, list):
            self.subscribed_events.difference_update(events)
    
    def is_subscribed(self, event: StreamEvent) -> bool:
        """Check if subscribed to event"""
        return event in self.subscribed_events or len(self.subscribed_events) == 0
    
    def set_filter(self, key: str, value: Any):
        """Set event filter"""
        self.filters[key] = value
    
    def matches_filter(self, message: StreamMessage) -> bool:
        """Check if message passes filters"""
        for key, value in self.filters.items():
            if key == 'correlation_id' and message.correlation_id != value:
                return False
            if key == 'source' and message.source != value:
                return False
            if key == 'min_level' and message.event in [StreamEvent.DEBUG_LOG, StreamEvent.DEBUG_ERROR]:
                # Level filtering for debug events
                pass
        return True


class WebSocketStreamingService:
    """
    Unified WebSocket streaming service.
    
    Manages client subscriptions and broadcasts messages
    from modular services to connected clients.
    
    Usage with Flask-SocketIO:
    ```python
    from flask_socketio import SocketIO
    streaming = WebSocketStreamingService()
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        streaming.subscribe(request.sid, data.get('events', 'all'))
    
    # In your service:
    streaming.emit(StreamEvent.COMMAND_OUTPUT, {'line': 'Hello'})
    ```
    """
    
    def __init__(self):
        """Initialize streaming service"""
        self.subscriptions: Dict[str, StreamSubscription] = {}
        self._emit_handler: Optional[Callable[[str, StreamMessage], None]] = None
        self._broadcast_handler: Optional[Callable[[StreamMessage], None]] = None
        
        # Message queue for buffering
        self._message_queue: List[StreamMessage] = []
        self._max_queue_size = 100
        
        # Stats
        self.total_messages = 0
        self.messages_by_event: Dict[str, int] = {}
    
    def set_emit_handler(self, handler: Callable[[str, StreamMessage], None]):
        """
        Set handler for emitting to specific client.
        
        Args:
            handler: Function(client_id, message) to emit message
        """
        self._emit_handler = handler
    
    def set_broadcast_handler(self, handler: Callable[[StreamMessage], None]):
        """
        Set handler for broadcasting to all clients.
        
        Args:
            handler: Function(message) to broadcast
        """
        self._broadcast_handler = handler
    
    # ─── Subscription Management ────────────────────────────────────
    
    def connect(self, client_id: str) -> StreamSubscription:
        """Handle client connection"""
        sub = StreamSubscription(client_id)
        self.subscriptions[client_id] = sub
        
        # Send welcome message
        self.emit_to(client_id, StreamEvent.CONNECT, {
            'message': 'Connected to uDOS streaming',
            'version': '1.2.30',
            'client_id': client_id,
        })
        
        return sub
    
    def disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
    
    def subscribe(self, client_id: str, events: List[str] | str, filters: Dict = None):
        """
        Subscribe client to events.
        
        Args:
            client_id: Client identifier
            events: Event names or "all"
            filters: Optional event filters
        """
        if client_id not in self.subscriptions:
            self.connect(client_id)
        
        sub = self.subscriptions[client_id]
        
        if events == "all":
            sub.subscribe("all")
        else:
            event_list = [StreamEvent(e) for e in events if e in [e.value for e in StreamEvent]]
            sub.subscribe(event_list)
        
        if filters:
            for key, value in filters.items():
                sub.set_filter(key, value)
    
    def unsubscribe(self, client_id: str, events: List[str] | str = "all"):
        """Unsubscribe client from events"""
        if client_id in self.subscriptions:
            sub = self.subscriptions[client_id]
            if events == "all":
                sub.unsubscribe("all")
            else:
                event_list = [StreamEvent(e) for e in events]
                sub.unsubscribe(event_list)
    
    def get_subscribers(self, event: StreamEvent = None) -> List[str]:
        """Get client IDs subscribed to event"""
        if event is None:
            return list(self.subscriptions.keys())
        return [
            cid for cid, sub in self.subscriptions.items()
            if sub.is_subscribed(event)
        ]
    
    # ─── Message Emission ───────────────────────────────────────────
    
    def emit(self, event: StreamEvent, data: Dict, correlation_id: str = None, source: str = None):
        """
        Emit event to all subscribed clients.
        
        Args:
            event: Event type
            data: Event payload
            correlation_id: Optional correlation ID
            source: Source service name
        """
        message = StreamMessage(
            event=event,
            data=data,
            correlation_id=correlation_id,
            source=source or "udos",
        )
        
        self._record_message(message)
        
        # Broadcast to subscribed clients
        for client_id, sub in self.subscriptions.items():
            if sub.is_subscribed(event) and sub.matches_filter(message):
                self._emit_to_client(client_id, message)
    
    def emit_to(self, client_id: str, event: StreamEvent, data: Dict, correlation_id: str = None):
        """Emit event to specific client"""
        message = StreamMessage(
            event=event,
            data=data,
            correlation_id=correlation_id,
        )
        
        self._record_message(message)
        self._emit_to_client(client_id, message)
    
    def broadcast(self, event: StreamEvent, data: Dict, correlation_id: str = None):
        """Broadcast event to ALL clients (ignoring subscriptions)"""
        message = StreamMessage(
            event=event,
            data=data,
            correlation_id=correlation_id,
        )
        
        self._record_message(message)
        
        if self._broadcast_handler:
            self._broadcast_handler(message)
        else:
            for client_id in self.subscriptions:
                self._emit_to_client(client_id, message)
    
    def _emit_to_client(self, client_id: str, message: StreamMessage):
        """Internal emit to single client"""
        if self._emit_handler:
            self._emit_handler(client_id, message)
        else:
            # Queue for later if no handler
            self._message_queue.append(message)
            if len(self._message_queue) > self._max_queue_size:
                self._message_queue = self._message_queue[-self._max_queue_size:]
    
    def _record_message(self, message: StreamMessage):
        """Record message stats"""
        self.total_messages += 1
        event_name = message.event.value
        self.messages_by_event[event_name] = self.messages_by_event.get(event_name, 0) + 1
    
    # ─── Service Integration Helpers ────────────────────────────────
    
    def emit_command_start(self, command: str, correlation_id: str = None):
        """Emit command start event"""
        self.emit(StreamEvent.COMMAND_START, {
            'command': command,
            'started_at': datetime.now().isoformat(),
        }, correlation_id)
    
    def emit_command_output(self, line: str, correlation_id: str = None):
        """Emit command output line"""
        self.emit(StreamEvent.COMMAND_OUTPUT, {
            'line': line,
        }, correlation_id)
    
    def emit_command_complete(self, result: Dict, correlation_id: str = None):
        """Emit command completion"""
        self.emit(StreamEvent.COMMAND_COMPLETE, result, correlation_id)
    
    def emit_command_error(self, error: str, correlation_id: str = None):
        """Emit command error"""
        self.emit(StreamEvent.COMMAND_ERROR, {
            'error': error,
        }, correlation_id)
    
    def emit_pager_content(self, lines: List[str], offset: int, total: int, correlation_id: str = None):
        """Emit pager content update"""
        self.emit(StreamEvent.PAGER_CONTENT, {
            'lines': lines,
            'offset': offset,
            'total': total,
        }, correlation_id)
    
    def emit_predictor_suggestions(self, input_text: str, predictions: List[Dict], correlation_id: str = None):
        """Emit predictor suggestions"""
        self.emit(StreamEvent.PREDICTOR_SUGGEST, {
            'input': input_text,
            'predictions': predictions,
        }, correlation_id)
    
    def emit_debug_log(self, entry: Dict, correlation_id: str = None):
        """Emit debug log entry"""
        self.emit(StreamEvent.DEBUG_LOG, entry, correlation_id)
    
    def emit_files_list(self, path: str, files: List[str], folders: List[str], correlation_id: str = None):
        """Emit file list update"""
        self.emit(StreamEvent.FILES_LIST, {
            'path': path,
            'files': files,
            'folders': folders,
        }, correlation_id)
    
    def emit_menu_action(self, action_id: str, metadata: Dict = None, correlation_id: str = None):
        """Emit menu action"""
        self.emit(StreamEvent.MENU_ACTION, {
            'action': action_id,
            'metadata': metadata or {},
        }, correlation_id)
    
    # ─── Stats & Status ─────────────────────────────────────────────
    
    def get_stats(self) -> Dict:
        """Get streaming statistics"""
        return {
            'connected_clients': len(self.subscriptions),
            'total_messages': self.total_messages,
            'messages_by_event': self.messages_by_event,
            'queue_size': len(self._message_queue),
        }
    
    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """Get client subscription info"""
        if client_id not in self.subscriptions:
            return None
        
        sub = self.subscriptions[client_id]
        return {
            'client_id': client_id,
            'subscribed_events': [e.value for e in sub.subscribed_events],
            'filters': sub.filters,
            'connected_at': sub.connected_at.isoformat(),
            'last_activity': sub.last_activity.isoformat(),
        }


# ─── Flask-SocketIO Integration ─────────────────────────────────────

def create_socketio_handlers(socketio, streaming_service: WebSocketStreamingService):
    """
    Create Flask-SocketIO event handlers.
    
    Usage:
    ```python
    from flask_socketio import SocketIO
    from dev.goblin.core.services.streaming_service import WebSocketStreamingService, create_socketio_handlers
    
    socketio = SocketIO(app)
    streaming = WebSocketStreamingService()
    create_socketio_handlers(socketio, streaming)
    ```
    """
    from flask import request
    from flask_socketio import emit
    
    # Set up emit handler
    def emit_to_client(client_id: str, message: StreamMessage):
        emit(message.event.value, message.to_dict(), room=client_id)
    
    streaming_service.set_emit_handler(emit_to_client)
    
    # Set up broadcast handler
    def broadcast_message(message: StreamMessage):
        emit(message.event.value, message.to_dict(), broadcast=True)
    
    streaming_service.set_broadcast_handler(broadcast_message)
    
    # Register handlers
    @socketio.on('connect')
    def handle_connect():
        streaming_service.connect(request.sid)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        streaming_service.disconnect(request.sid)
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        events = data.get('events', 'all')
        filters = data.get('filters', {})
        streaming_service.subscribe(request.sid, events, filters)
        emit('subscribed', {'events': events, 'filters': filters})
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        events = data.get('events', 'all')
        streaming_service.unsubscribe(request.sid, events)
        emit('unsubscribed', {'events': events})


# ─── Convenience Functions ──────────────────────────────────────────

_service_instance: WebSocketStreamingService = None

def get_streaming_service() -> WebSocketStreamingService:
    """Get singleton streaming service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = WebSocketStreamingService()
    return _service_instance


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    service = WebSocketStreamingService()
    
    # Simulate connections
    service.connect('client-1')
    service.connect('client-2')
    
    # Subscribe
    service.subscribe('client-1', ['command_output', 'debug_log'])
    service.subscribe('client-2', 'all')
    
    print(f"Connected clients: {len(service.subscriptions)}")
    print(f"Subscribers to COMMAND_OUTPUT: {service.get_subscribers(StreamEvent.COMMAND_OUTPUT)}")
    
    # Test emit (no handler, so will queue)
    service.emit_command_output("Hello, World!")
    service.emit_debug_log({'level': 'INFO', 'message': 'Test log'})
    
    print(f"\nStats: {service.get_stats()}")
    print(f"\nClient-1 info: {service.get_client_info('client-1')}")
