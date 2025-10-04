"""
Generic PUB/SUB subscriber for debugging.
Subscribes to a ZMQ PUB endpoint and prints received messages.
"""

import os
import sys
import signal
import zmq
import typer
import json
from typing import Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.logging_utils import log_message, setup_pretty_logging

# Load environment variables
load_dotenv()

app = typer.Typer()


class PrintSubscriber:
    """Generic subscriber that prints received messages"""
    
    def __init__(self, endpoint: str, topic: str = "", pretty: bool = False):
        self.endpoint = endpoint
        self.topic = topic
        self.pretty = pretty
        self.running = True
        
        # ZMQ context and socket
        self.context = zmq.Context()
        self.sub_socket = None
        
        # Statistics
        self.messages_received = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    def _setup_socket(self):
        """Setup ZMQ SUB socket"""
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(self.endpoint)
        
        if self.topic:
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, self.topic.encode())
            print(f"📡 Subscribed to topic '{self.topic}' on {self.endpoint}")
        else:
            self.sub_socket.setsockopt(zmq.SUBSCRIBE, b"")
            print(f"📡 Subscribed to all topics on {self.endpoint}")
    
    def _print_message(self, message_data: bytes):
        """Print received message"""
        try:
            # Parse the message (skip topic prefix if present)
            if b' ' in message_data:
                topic, message_json = message_data.split(b' ', 1)
                topic_str = topic.decode('utf-8')
                message_str = message_json.decode('utf-8')
            else:
                topic_str = "NO_TOPIC"
                message_str = message_data.decode('utf-8')
            
            # Try to parse as JSON
            try:
                message_obj = json.loads(message_str)
                if self.pretty:
                    print(f"\n📨 Topic: {topic_str}")
                    print(f"📄 Message:")
                    print(json.dumps(message_obj, indent=2, ensure_ascii=False))
                else:
                    print(f"TOPIC:{topic_str} | {json.dumps(message_obj, ensure_ascii=False)}")
            except json.JSONDecodeError:
                # Not JSON, print as plain text
                if self.pretty:
                    print(f"\n📨 Topic: {topic_str}")
                    print(f"📄 Message: {message_str}")
                else:
                    print(f"TOPIC:{topic_str} | {message_str}")
            
            self.messages_received += 1
            
        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")
    
    def run(self):
        """Main run loop"""
        try:
            self._setup_socket()
            
            print(f"🚀 Print subscriber started!")
            print(f"📊 Endpoint: {self.endpoint}")
            print(f"🏷️  Topic filter: {self.topic if self.topic else 'ALL'}")
            print(f"🎨 Pretty mode: {'ON' if self.pretty else 'OFF'}")
            print(f"⏹️  Press Ctrl+C to stop")
            print(f"{'='*60}")
            
            while self.running:
                try:
                    # Poll for messages with timeout
                    if self.sub_socket.poll(1000):  # 1 second timeout
                        message_data = self.sub_socket.recv()
                        self._print_message(message_data)
                    
                except zmq.Again:
                    # Timeout, continue
                    continue
                except Exception as e:
                    print(f"❌ Error in main loop: {str(e)}")
                    break
            
        except Exception as e:
            print(f"💥 Fatal error: {str(e)}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        if self.sub_socket:
            self.sub_socket.close()
        if self.context:
            self.context.term()
        
        print(f"\n📊 Statistics:")
        print(f"   Messages received: {self.messages_received}")
        print(f"✅ Print subscriber stopped")


@app.command()
def main(
    endpoint: str = typer.Argument(..., help="ZMQ PUB endpoint (e.g., tcp://127.0.0.1:5556)"),
    topic: str = typer.Option("", "--topic", help="Topic to subscribe to (empty for all topics)"),
    pretty: bool = typer.Option(False, "--pretty", help="Use pretty output format")
):
    """
    Generic PUB/SUB subscriber for debugging.
    
    Examples:
        # Subscribe to all topics from GC PUB
        python tools/print_subscriber.py tcp://127.0.0.1:5556
        
        # Subscribe only to RENOVACION topic
        python tools/print_subscriber.py tcp://127.0.0.1:5556 --topic RENOVACION
        
        # Pretty output
        python tools/print_subscriber.py tcp://127.0.0.1:5556 --pretty
    """
    if pretty:
        setup_pretty_logging()
    
    subscriber = PrintSubscriber(endpoint=endpoint, topic=topic, pretty=pretty)
    subscriber.run()


if __name__ == "__main__":
    app()
