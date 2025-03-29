#!/usr/bin/env python3
"""
Helper script for interacting with Claude's API with the system prompt automatically included.
This script provides functions to easily include the system prompt in API calls to Claude.
"""

import os
import json
import requests
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Path to the system prompt
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "docs" / "system-prompt" / "system-prompt.md"

def get_system_prompt():
    """
    Get the system prompt from either the environment variable or the file.
    Returns the system prompt as a string.
    """
    # First try to get it from the environment variable
    system_prompt = os.environ.get("CLAUDE_SYSTEM_PROMPT")
    
    # If not found in environment, read from file
    if not system_prompt:
        if SYSTEM_PROMPT_PATH.exists():
            with open(SYSTEM_PROMPT_PATH, "r") as f:
                system_prompt = f.read()
        else:
            raise FileNotFoundError(f"System prompt file not found at {SYSTEM_PROMPT_PATH}")
    
    return system_prompt

def create_claude_message(user_message, include_system_prompt=True):
    """
    Create a message for Claude's API with the system prompt included.
    
    Args:
        user_message (str): The user's message to Claude
        include_system_prompt (bool): Whether to include the system prompt
        
    Returns:
        dict: A dictionary with the message content formatted for Claude's API
    """
    messages = []
    
    # Add system prompt if requested
    if include_system_prompt:
        try:
            system_prompt = get_system_prompt()
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        except Exception as e:
            print(f"Warning: Could not include system prompt: {e}")
    
    # Add user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages

def call_claude_api(user_message, api_key=None, model="claude-3-opus-20240229", include_system_prompt=True):
    """
    Call Claude's API with the user message and system prompt.
    
    Args:
        user_message (str): The user's message to Claude
        api_key (str): The API key for Claude. If None, will try to get from ANTHROPIC_API_KEY environment variable
        model (str): The Claude model to use
        include_system_prompt (bool): Whether to include the system prompt
        
    Returns:
        dict: The response from Claude's API
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key not provided and ANTHROPIC_API_KEY environment variable not set")
    
    # Create messages
    messages = create_claude_message(user_message, include_system_prompt)
    
    # Create request payload
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096
    }
    
    # Call API
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload
    )
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")
    
    return response.json()

def get_claude_response(user_message, api_key=None, model="claude-3-opus-20240229", include_system_prompt=True):
    """
    Get a response from Claude with the system prompt included.
    
    Args:
        user_message (str): The user's message to Claude
        api_key (str): The API key for Claude. If None, will try to get from ANTHROPIC_API_KEY environment variable
        model (str): The Claude model to use
        include_system_prompt (bool): Whether to include the system prompt
        
    Returns:
        str: The response content from Claude
    """
    response = call_claude_api(user_message, api_key, model, include_system_prompt)
    return response["content"][0]["text"]

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Helper script for interacting with Claude's API")
    parser.add_argument("message", nargs="?", help="Message to send to Claude")
    parser.add_argument("--no-system-prompt", action="store_true", help="Don't include the system prompt")
    parser.add_argument("--model", default="claude-3-opus-20240229", help="Claude model to use")
    parser.add_argument("--api-key", help="API key for Claude (if not provided, will use ANTHROPIC_API_KEY environment variable)")
    
    args = parser.parse_args()
    
    # If no message provided, read from stdin
    if not args.message:
        print("Enter your message to Claude (Ctrl+D to finish):")
        message_lines = []
        try:
            while True:
                line = input()
                message_lines.append(line)
        except EOFError:
            pass
        args.message = "\n".join(message_lines)
    
    try:
        response = get_claude_response(
            args.message,
            api_key=args.api_key,
            model=args.model,
            include_system_prompt=not args.no_system_prompt
        )
        print("\nClaude's response:")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
