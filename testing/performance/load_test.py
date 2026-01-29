"""
Load Testing Script using Locust
Tests system under various load conditions
"""

from locust import HttpUser, task, between
import json
import random


class VoiceAgentUser(HttpUser):
    """Simulates a user interacting with the voice agent"""
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.room_name = f"load-test-room-{random.randint(1000, 9999)}"
        self.token = None
        
        # Generate token
        response = self.client.post(
            "/api/livekit-token",
            json={"room_name": self.room_name}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
    
    @task(3)
    def generate_token(self):
        """Generate a new token (high frequency)"""
        room_name = f"test-room-{random.randint(1000, 9999)}"
        self.client.post(
            "/api/livekit-token",
            json={"room_name": room_name},
            name="Generate Token"
        )
    
    @task(2)
    def verify_token(self):
        """Verify token (medium frequency)"""
        if self.token:
            self.client.post(
                "/api/auth/verify",
                json={"token": self.token},
                name="Verify Token"
            )
    
    @task(1)
    def get_conversations(self):
        """Get conversations (low frequency, requires auth)"""
        if self.token:
            self.client.get(
                "/api/conversations",
                headers={"Authorization": f"Bearer {self.token}"},
                name="Get Conversations"
            )


# Run with: locust -f load_test.py --host=http://localhost:3000


