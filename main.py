#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime
import anthropic
import random

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_USER = "promptfactory55@gmail.com"

CATEGORIES = ["marketing/sales", "entrepreneurship", "development"]
PRICES = {"marketing/sales": 9.99, "entrepreneurship": 11.99, "development": 12.99}

def generate_prompt(category):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt_text = f"Create a JSON prompt for {category} with: title, description, prompt_content, use_case"
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt_text}]
    )
    return response.content[0].text

def main():
    print("PromptFactory Started")
    category = random.choice(CATEGORIES)
    print(f"Selected: {category}")
    result = generate_prompt(category)
    print(f"Generated: {result}")
    print("Done!")

if __name__ == "__main__":
    main()
