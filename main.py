#!/usr/bin/env python3
import os
import json
import random
from datetime import datetime
from anthropic import Anthropic
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Initialize Anthropic client
client = Anthropic()

# Get API keys from environment
GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Configuration
CATEGORIES = ["marketing", "entrepreneur", "developer"]
PRICES = {"marketing": 9.99, "entrepreneur": 12.99, "developer": 7.99}

def get_category_for_today():
    """Determine which category to use based on the day"""
    day_of_week = datetime.now().weekday()
    category_index = day_of_week % len(CATEGORIES)
    return CATEGORIES[category_index]

def generate_prompt(category):
    """Generate a high-quality prompt using Claude"""
    
    category_descriptions = {
        "marketing": "Create a professional marketing/sales prompt that helps businesses improve their customer acquisition and retention strategies",
        "entrepreneur": "Create an actionable entrepreneurship prompt that helps founders develop business ideas, strategies, or solve operational challenges",
        "developer": "Create a technical prompt that helps software developers improve their coding skills, solve problems, or learn new technologies"
    }
    
    prompt_request = f"""
    Generate a unique, high-quality prompt template for the {category} category.
    
    Requirements:
    - Professional and actionable
    - Can be used by users in their daily work
    - Should take 5-10 minutes to fully utilize
    - Include clear instructions and examples
    - Make it valuable and immediately useful
    
    Category context: {category_descriptions[category]}
    
    Format the response as:
    TITLE: [Catchy title]
    DESCRIPTION: [2-3 sentence description]
    PROMPT: [The actual prompt template]
    USE_CASE: [1-2 sentence use case]
    """
    
    message =
