// WebSocket connection management

import { WebSocketMessage } from '../types/api';

interface WebSocketEventHandlers {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onReconnect?: (attempt: number) => void;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: WebSocketEventHandlers = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private shouldReconnect = true;

  constructor(url?: string) {
    this.url = url || process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000/ws';
  }

  // Connect to WebSocket
  connect(handlers: WebSocketEventHandlers = {}) {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.handlers = handlers;
    this.isConnecting = true;
    this.shouldReconnect = true;

    try {
      // In mock mode, don't actually create WebSocket
      if (process.env.REACT_APP_MOCK_MODE === 'true') {
        this.setupMockWebSocket();
        return;
      }

      this.ws = new WebSocket(this.url);
      this.setupEventListeners();
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  // Disconnect from WebSocket
  disconnect() {
    this.shouldReconnect = false;
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  // Send message through WebSocket
  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }

  // Get connection status
  getStatus(): 'connecting' | 'open' | 'closing' | 'closed' {
    if (!this.ws) return 'closed';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'open';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'closed';
    }
  }

  // Check if connected
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Private methods
  private setupEventListeners() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.handlers.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handlers.onMessage?.(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.isConnecting = false;
      this.ws = null;
      this.handlers.onDisconnect?.();
      
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
      this.handlers.onError?.(error);
    };
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.shouldReconnect) {
        this.handlers.onReconnect?.(this.reconnectAttempts);
        this.connect(this.handlers);
      }
    }, delay);
  }

  // Mock WebSocket implementation for development
  private setupMockWebSocket() {
    console.log('Mock WebSocket connected');
    this.isConnecting = false;
    this.handlers.onConnect?.();

    // Simulate periodic messages
    this.startMockMessageTimer();
  }

  private startMockMessageTimer() {
    const sendMockMessage = () => {
      if (!this.shouldReconnect) return;

      const mockMessages: WebSocketMessage[] = [
        {
          type: 'entity_update',
          data: {
            entity_id: 'employee_1',
            action: 'updated',
            changes: ['salary']
          },
          timestamp: new Date().toISOString()
        },
        {
          type: 'calculation_complete',
          data: {
            calculation_type: 'forecast',
            duration_ms: 1234,
            status: 'success'
          },
          timestamp: new Date().toISOString()
        },
        {
          type: 'system_status',
          data: {
            status: 'healthy',
            entities_count: 10,
            last_calculation: new Date().toISOString()
          },
          timestamp: new Date().toISOString()
        }
      ];

      // Send random message every 10-30 seconds
      const randomMessage = mockMessages[Math.floor(Math.random() * mockMessages.length)];
      this.handlers.onMessage?.(randomMessage);

      if (this.shouldReconnect) {
        setTimeout(sendMockMessage, 10000 + Math.random() * 20000);
      }
    };

    // Start sending messages after a delay
    setTimeout(sendMockMessage, 5000);
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

// Export the class as well for direct instantiation if needed
export { WebSocketService };

// Hook for React components
export function useWebSocket(handlers: WebSocketEventHandlers) {
  return {
    connect: () => websocketService.connect(handlers),
    disconnect: () => websocketService.disconnect(),
    send: (message: any) => websocketService.send(message),
    status: websocketService.getStatus(),
    isConnected: websocketService.isConnected()
  };
}

export default websocketService;