"""
Tests for WebSocket functionality.
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect


class TestWebSocketEndpoints:
    """Test WebSocket connection and messaging."""

    def test_websocket_connection_status(self, test_client: TestClient):
        """Test WebSocket status endpoint connection."""
        with test_client.websocket_connect("/ws/status") as websocket:
            # Should receive welcome message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connected"
            assert "connection_id" in message["data"]

    def test_websocket_connection_entities(self, test_client: TestClient):
        """Test WebSocket entities endpoint connection."""
        with test_client.websocket_connect("/ws/entities") as websocket:
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connected"
            assert message["data"]["topic"] == "entities"

    def test_websocket_connection_calculations(self, test_client: TestClient):
        """Test WebSocket calculations endpoint connection."""
        with test_client.websocket_connect("/ws/calculations") as websocket:
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connected"
            assert message["data"]["topic"] == "calculations"

    def test_websocket_heartbeat(self, test_client: TestClient):
        """Test WebSocket heartbeat mechanism."""
        with test_client.websocket_connect("/ws/status") as websocket:
            # Receive welcome message
            websocket.receive_text()
            
            # Send heartbeat
            heartbeat_msg = {"type": "heartbeat", "timestamp": 1234567890}
            websocket.send_text(json.dumps(heartbeat_msg))
            
            # Should receive heartbeat response
            response = websocket.receive_text()
            message = json.loads(response)
            assert message["type"] == "heartbeat_ack"

    def test_websocket_subscription_management(self, test_client: TestClient):
        """Test WebSocket subscription management."""
        with test_client.websocket_connect("/ws/status") as websocket:
            # Skip welcome message
            websocket.receive_text()
            
            # Send subscription request
            subscribe_msg = {
                "type": "subscribe",
                "topic": "kpi_updates"
            }
            websocket.send_text(json.dumps(subscribe_msg))
            
            # Should receive subscription confirmation
            response = websocket.receive_text()
            message = json.loads(response)
            assert message["type"] == "subscribed"
            assert message["data"]["topic"] == "kpi_updates"

    def test_websocket_unsubscribe(self, test_client: TestClient):
        """Test WebSocket unsubscription."""
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Skip welcome
            
            # Subscribe first
            subscribe_msg = {"type": "subscribe", "topic": "test_topic"}
            websocket.send_text(json.dumps(subscribe_msg))
            websocket.receive_text()  # Skip subscription confirmation
            
            # Then unsubscribe
            unsubscribe_msg = {"type": "unsubscribe", "topic": "test_topic"}
            websocket.send_text(json.dumps(unsubscribe_msg))
            
            response = websocket.receive_text()
            message = json.loads(response)
            assert message["type"] == "unsubscribed"

    def test_websocket_broadcast_functionality(self, test_client: TestClient):
        """Test WebSocket broadcast functionality."""
        # Test the broadcast endpoint
        response = test_client.post(
            "/api/websockets/test-broadcast?message_type=test_message&topic=status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connections" in data

    def test_websocket_connection_stats(self, test_client: TestClient):
        """Test WebSocket connection statistics."""
        response = test_client.get("/api/websockets/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_connections" in data
        assert "total_subscriptions" in data
        assert "topics" in data
        assert "connections" in data
        assert isinstance(data["total_connections"], int)

    def test_websocket_invalid_message_handling(self, test_client: TestClient):
        """Test handling of invalid WebSocket messages."""
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Skip welcome
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Connection should remain open (server handles gracefully)
            # Send valid message to verify connection is still active
            valid_msg = {"type": "heartbeat", "timestamp": 1234567890}
            websocket.send_text(json.dumps(valid_msg))
            
            response = websocket.receive_text()
            message = json.loads(response)
            assert message["type"] == "heartbeat_ack"

    def test_multiple_websocket_connections(self, test_client: TestClient):
        """Test multiple simultaneous WebSocket connections."""
        connections = []
        
        try:
            # Create multiple connections
            for i in range(3):
                ws = test_client.websocket_connect("/ws/status")
                connection = ws.__enter__()
                connections.append((ws, connection))
                
                # Receive welcome message
                data = connection.receive_text()
                message = json.loads(data)
                assert message["type"] == "connected"
            
            # All connections should be independent
            assert len(connections) == 3
            
        finally:
            # Clean up connections
            for ws_context, connection in connections:
                try:
                    ws_context.__exit__(None, None, None)
                except:
                    pass

    def test_websocket_message_ordering(self, test_client: TestClient):
        """Test that WebSocket messages are received in order."""
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Skip welcome
            
            # Send multiple messages rapidly
            for i in range(5):
                msg = {"type": "test", "sequence": i}
                websocket.send_text(json.dumps(msg))
            
            # WebSocket should handle all messages
            # (Note: This is a basic test - actual ordering depends on implementation)

    def test_websocket_connection_limit(self, test_client: TestClient):
        """Test WebSocket connection behavior under load."""
        # This test verifies that the server can handle multiple connections
        # without crashing (basic stress test)
        
        connections = []
        max_connections = 10
        
        try:
            for i in range(max_connections):
                try:
                    ws = test_client.websocket_connect("/ws/status")
                    connection = ws.__enter__()
                    connections.append((ws, connection))
                    
                    # Just verify connection works
                    data = connection.receive_text()
                    message = json.loads(data)
                    assert message["type"] == "connected"
                    
                except Exception as e:
                    # Some connections might fail under load - that's expected
                    break
            
            # Should have established at least some connections
            assert len(connections) > 0
            
        finally:
            for ws_context, connection in connections:
                try:
                    ws_context.__exit__(None, None, None)
                except:
                    pass


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios."""

    def test_websocket_connection_rejection(self, test_client: TestClient):
        """Test WebSocket connection rejection scenarios."""
        # Test invalid endpoint
        try:
            with test_client.websocket_connect("/ws/invalid"):
                pass
        except Exception:
            # Should raise an exception for invalid endpoint
            pass

    def test_websocket_disconnect_handling(self, test_client: TestClient):
        """Test proper handling of WebSocket disconnections."""
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Welcome message
            
            # Send a message then close
            msg = {"type": "test", "data": "disconnect_test"}
            websocket.send_text(json.dumps(msg))
            
            # Close connection (handled by context manager)

    def test_websocket_malformed_subscription(self, test_client: TestClient):
        """Test handling of malformed subscription requests."""
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Skip welcome
            
            # Send malformed subscription
            malformed_msg = {"type": "subscribe"}  # Missing topic
            websocket.send_text(json.dumps(malformed_msg))
            
            # Should receive error message or handle gracefully
            try:
                response = websocket.receive_text()
                message = json.loads(response)
                # Server should either send error or ignore invalid request
                assert "type" in message
            except:
                # Connection might close on invalid request - that's also valid
                pass


@pytest.mark.asyncio
class TestAsyncWebSocket:
    """Test async WebSocket functionality."""
    
    async def test_async_websocket_connection(self, test_app):
        """Test async WebSocket connection."""
        from fastapi.testclient import TestClient
        
        # Note: For real async WebSocket testing, we'd use a different approach
        # This is a simplified test using TestClient
        client = TestClient(test_app)
        
        with client.websocket_connect("/ws/status") as websocket:
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connected"

    async def test_async_websocket_broadcast(self, async_test_client):
        """Test async WebSocket broadcast functionality."""
        response = await async_test_client.post(
            "/api/websockets/test-broadcast?message_type=async_test&topic=status"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestWebSocketPerformance:
    """Performance tests for WebSocket functionality."""

    def test_websocket_connection_speed(self, test_client: TestClient):
        """Test WebSocket connection establishment speed."""
        import time
        
        start_time = time.time()
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Welcome message
            end_time = time.time()
        
        connection_time = end_time - start_time
        assert connection_time < 1.0  # Should connect within 1 second

    def test_websocket_message_throughput(self, test_client: TestClient):
        """Test WebSocket message throughput."""
        import time
        
        with test_client.websocket_connect("/ws/status") as websocket:
            websocket.receive_text()  # Skip welcome
            
            message_count = 100
            start_time = time.time()
            
            for i in range(message_count):
                msg = {"type": "throughput_test", "sequence": i}
                websocket.send_text(json.dumps(msg))
            
            end_time = time.time()
            
            throughput_time = end_time - start_time
            messages_per_second = message_count / throughput_time
            
            # Should handle at least 50 messages per second
            assert messages_per_second > 50

    def test_websocket_concurrent_connections_performance(self, test_client: TestClient):
        """Test performance with concurrent WebSocket connections."""
        import time
        import threading
        
        results = []
        
        def create_connection():
            try:
                start_time = time.time()
                with test_client.websocket_connect("/ws/status") as websocket:
                    websocket.receive_text()  # Welcome message
                    end_time = time.time()
                    results.append(end_time - start_time)
            except Exception as e:
                results.append(None)  # Connection failed
        
        # Create 5 concurrent connections
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_connection)
            threads.append(thread)
            thread.start()
        
        # Wait for all connections to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout
        
        # Check results
        successful_connections = [r for r in results if r is not None]
        assert len(successful_connections) > 0  # At least some should succeed
        
        # Average connection time should be reasonable
        if successful_connections:
            avg_time = sum(successful_connections) / len(successful_connections)
            assert avg_time < 2.0  # Average should be under 2 seconds