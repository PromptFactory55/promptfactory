#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_USER = "promptfactory55@gmail.com"

CATEGORIES = ["marketing/sales", "entrepreneurship", "development"]
PRICES = {"marketing/sales": 9.99, "entrepreneurship": 11.99, "development": 12.99}

def generate_prompt(category: str) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt_request = f"You are a professional prompt engineer for {category}. Generate a high-quality prompt. Return ONLY valid JSON: {{\"title\": \"title\", \"description\": \"desc\", \"prompt_content\": \"content\", \"use_case\": \"use\"}}"
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt_request}]
    )
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    prompt_data = json.loads(response_text)
    prompt_data["category"] = category
    prompt_data["price"] = PRICES[category]
    prompt_data["timestamp"] = datetime.now().isoformat()
    return prompt_data

def create_gumroad_product(prompt_data: dict) -> str:
    headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}", "Content-Type": "application/json"}
    payload = {"name": prompt_data["title"], "description": prompt_data["description"], "price": prompt_data["price"], "currency": "usd", "content": prompt_data["prompt_content"]}
    response = requests.post("https://api.gumroad.com/v2/products", headers=headers, json=payload)
    if response.status_code == 201:
        product_id = response.json()["product"]["id"]
        print(f"✅ Gumroad product created: {product_id}")
        return product_id
    else:
        print(f"❌ Gumroad error: {response.status_code}")
        return None

def post_to_twitter(prompt_data: dict, product_url: str) -> bool:
    try:
        from twitter import Api
        api = Api(consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET, sleep_on_rate_limit=True)
        tweet_text = f"🚀 New prompt: {prompt_data['title']}\nPrice: ${prompt_data['price']}\n{product_url}\n#AI"
        status = api.PostUpdate(tweet_text)
        print(f"✅ Tweet posted: {status.id}")
        return True
    except Exception as e:
        print(f"⚠️ Twitter error: {e}")
        return False

def log_sales_data(prompt_data: dict, product_id: str):
    log_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_id": product_id,
        "title": prompt_data["title"],
        "category": prompt_data["category"],
        "price": prompt_data["price"]
    }
    log_file = "sales_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []
    logs.append(log_entry)
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)
    print("📊 Sales log updated")

def send_daily_report(prompt_data: dict):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER
        msg["Subject"] = f"PromptFactory Report - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"Generated: {prompt_data['title']}\nCategory: {prompt_data['category']}\nPrice: ${prompt_data['price']}"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Report sent")
    except Exception as e:
        print(f"⚠️ Email error: {e}")

def main():
    print("🚀 PromptFactory Started")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        category = random.choice(CATEGORIES)
        print(f"📂 Category: {category}")
        print("🤖 Generating prompt...")
        prompt_data = generate_prompt(category)
        print(f"✅ Generated: {prompt_data['title']}")
        print("🛒 Creating Gumroad product...")
        product_id = create_gumroad_product(prompt_data)
        if not product_id:
            print("❌ Failed")
            return
        product_url = f"https://gumroad.com/l/{product_id}"
        print("📱 Posting to X...")
        post_to_twitter(prompt_data, product_url)
        print("📊 Logging...")
        log_sales_data(prompt_data, product_id)
        print("📧 Reporting...")
        send_daily_report(prompt_data)
        print("✅ Completed!")
        print(f"📦 {product_url}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
