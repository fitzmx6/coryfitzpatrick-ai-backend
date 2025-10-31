#!/usr/bin/env python3
"""
Interactive chat client for Cory's AI Portfolio Chatbot
Connects to the streaming API and maintains conversation history
"""

import requests
import sys
import json

# API Configuration
API_URL = "http://localhost:8000/api/chat/stream"
# For production, set this to your Cloud Run service URL

def print_welcome():
    """Display welcome message"""
    print("\n" + "="*60)
    print("Welcome to Cory Fitzpatrick's AI Portfolio Chatbot!")
    print("="*60)
    print("\nAsk me anything about Cory's:")
    print("  • Work experience and achievements")
    print("  • Technical skills and expertise")
    print("  • Leadership philosophy and approach")
    print("  • Contact information")
    print("\nType 'quit' or 'exit' to end the conversation\n")
    print("="*60 + "\n")

def send_question(question, conversation_history):
    """
    Send question to the streaming API and print response in real-time

    Args:
        question: User's question
        conversation_history: List of previous messages

    Returns:
        The complete response text
    """
    payload = {
        "message": question,
        "conversation_history": conversation_history
    }

    try:
        # Send request with streaming enabled
        response = requests.post(
            API_URL,
            json=payload,
            stream=True,
            timeout=30
        )
        response.raise_for_status()

        # Print response as it streams in
        print("\nCory's AI Assistant: ", end="", flush=True)
        full_response = ""

        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                print(chunk, end="", flush=True)
                full_response += chunk

        print("\n")  # New line after response
        return full_response

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the chatbot API.")
        print("Make sure the server is running at:", API_URL)
        return None
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return None

def main():
    """Main chat loop"""
    print_welcome()

    # Store conversation history
    conversation_history = []

    while True:
        # Get user input
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! Thanks for chatting!")
            sys.exit(0)

        # Check for exit commands
        if question.lower() in ['quit', 'exit', 'bye', 'q']:
            print("\nGoodbye! Thanks for chatting!")
            break

        # Skip empty questions
        if not question:
            continue

        # Send question and get response
        response = send_question(question, conversation_history)

        if response is None:
            # Error occurred, ask if user wants to try again
            retry = input("\nWould you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                break
            continue

        # Update conversation history
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
