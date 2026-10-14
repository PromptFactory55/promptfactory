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
    prompt_text = f"Create a JSON prompt for {category}"
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
    print("Success!")

main()

def post_to_twitter(prompt_text, product_url):
    import tweepy
    
    auth = tweepy.OAuthHandler(os.getenv("TWITTER_CONSUMER_KEY"), os.getenv("TWITTER_CONSUMER_SECRET"))
    auth.set_access_token(os.getenv("TWITTER_ACCESS_TOKEN"), os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)
    
    post = f"📝 New prompt available!\n\n{prompt_text[:100]}...\n\n🔗 {product_url}\n\n#PromptFactory"
    api.update_status(post)
    print("Posted to Twitter!")
