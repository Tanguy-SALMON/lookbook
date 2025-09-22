#!/usr/bin/env python3
"""
Chat Demo Script

Simple interactive demo to test the chat functionality directly.
Shows real-time chat responses for various fashion queries.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app


def print_separator():
    """Print a visual separator."""
    print("=" * 80)


def print_chat_message(role: str, message: str):
    """Print a formatted chat message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if role == "USER":
        print(f"[{timestamp}] 👤 YOU: {message}")
    else:
        print(f"[{timestamp}] 🤖 AI: {message}")


def test_chat_queries():
    """Test various chat queries and show responses."""
    client = TestClient(app)

    print("🤖 LOOKBOOK-MPC CHAT DEMO")
    print_separator()
    print("Testing various fashion chat queries...")
    print_separator()

    # Test queries that represent real user interactions
    test_queries = [
        "hello",
        "I want to see my friend Saturday night",
        "I need something for yoga",
        "business meeting tomorrow",
        "I want to look slim",
        "red dress under 2000 baht",
        "casual weekend outfit",
        "party dress",
        "beach vacation clothes",
        "what should I wear to work?",
    ]

    session_id = None

    for query in test_queries:
        print_chat_message("USER", query)

        # Prepare request
        request_data = {"message": query}
        if session_id:
            request_data["session_id"] = session_id

        try:
            # Send chat request
            response = client.post("/v1/chat", json=request_data)

            if response.status_code == 200:
                data = response.json()

                # Store session ID for continuity
                if not session_id:
                    session_id = data.get("session_id")

                # Print AI response
                if data.get("replies") and len(data["replies"]) > 0:
                    reply_message = data["replies"][0].get("message", "No response")
                    print_chat_message("AI", reply_message)

                    # Show if outfits were recommended
                    if data.get("outfits"):
                        print(
                            f"     ✨ {len(data['outfits'])} outfit recommendations included"
                        )
                else:
                    print_chat_message("AI", "No reply received")

            else:
                print_chat_message(
                    "AI", f"Error {response.status_code}: {response.text}"
                )

        except Exception as e:
            print_chat_message("AI", f"Error: {str(e)}")

        print()  # Add spacing between interactions

    print_separator()
    print("💡 DEMO COMPLETE!")
    print(f"Session ID used: {session_id}")
    print("\nTo start the full server with web interface:")
    print("./start_server.sh")
    print("\nThen visit: http://localhost:8000/demo")
    print_separator()


def interactive_chat():
    """Run interactive chat session."""
    client = TestClient(app)
    session_id = None

    print("🤖 LOOKBOOK-MPC INTERACTIVE CHAT")
    print_separator()
    print("Type your fashion questions below. Type 'quit' to exit.")
    print_separator()

    while True:
        try:
            # Get user input
            user_input = input("\n👤 YOU: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print_chat_message(
                    "AI", "Goodbye! Thanks for trying the fashion chat demo!"
                )
                break

            if not user_input:
                continue

            # Prepare request
            request_data = {"message": user_input}
            if session_id:
                request_data["session_id"] = session_id

            # Send chat request
            response = client.post("/v1/chat", json=request_data)

            if response.status_code == 200:
                data = response.json()

                # Store session ID for continuity
                if not session_id:
                    session_id = data.get("session_id")

                # Print AI response
                if data.get("replies") and len(data["replies"]) > 0:
                    reply_message = data["replies"][0].get("message", "No response")
                    print_chat_message("AI", reply_message)

                    # Show if outfits were recommended
                    if data.get("outfits"):
                        print(
                            f"     ✨ {len(data['outfits'])} outfit recommendations included"
                        )
                else:
                    print_chat_message("AI", "No reply received")

            else:
                print_chat_message(
                    "AI",
                    f"Error {response.status_code}: Please try rephrasing your question.",
                )

        except KeyboardInterrupt:
            print("\n")
            print_chat_message("AI", "Chat session ended. Thanks for trying the demo!")
            break
        except Exception as e:
            print_chat_message("AI", f"Sorry, I encountered an error: {str(e)}")


def main():
    """Main function with options."""
    import argparse

    parser = argparse.ArgumentParser(description="Chat Demo for Lookbook-MPC")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run interactive chat session"
    )
    parser.add_argument(
        "--test", "-t", action="store_true", help="Run automated test queries (default)"
    )

    args = parser.parse_args()

    if args.interactive:
        interactive_chat()
    else:
        test_chat_queries()


if __name__ == "__main__":
    main()
