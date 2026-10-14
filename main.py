```python
#!/usr/bin/env python3
"""
PromptFactory - Daily Automated Prompt Generation & Sales System
Generates prompts, creates Gumroad products, posts to X, logs sales
"""

import os
import json
import requests
from datetime import datetime
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# API Keys & Credentials
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GUMROAD_TOKEN = os.getenv("GUMROAD_TOKEN")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
GMAIL_USER = "promptfactory55@gmail.com"

# Configuration
CATEGORIES = ["marketing/sales", "entrepreneurship", "development"]
PRICES = {"marketing/sales": 9.99, "entrepreneurship": 11.99, "development": 12.99}

def generate_prompt(category: str) -> dict:
"""Claude を使ってプロンプトを生成"""
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

prompt_request = f"""
You are a professional prompt engineer for {category}.
Generate a high-quality, practical prompt that users will want to buy.

Return ONLY valid JSON (no markdown, no extra text):
{{
"title": "Clear, engaging title",
"description": "Brief description (1-2 sentences)",
"prompt_content": "The actual prompt text (200-300 words)",
"use_case": "Primary use case"
}}
"""

message = client.messages.create(
model="claude-3-5-sonnet-20241022",
max_tokens=1024,
messages=[
{"role": "user", "content": prompt_request}
]
)

response_text = message.content[0].text.strip()

# Clean up markdown if present
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
"""Gumroad に商品を作成"""
headers = {
"Authorization": f"Bearer {GUMROAD_TOKEN}",
"Content-Type": "application/json"
}

payload = {
"name": prompt_data["title"],
"description": prompt_data["description"],
"price": prompt_data["price"],
"currency": "usd",
"content": prompt_data["prompt_content"]
}

response = requests.post(
"https://api.gumroad.com/v2/products",
headers=headers,
json=payload
)

if response.status_code == 201:
product_id = response.json()["product"]["id"]
print(f"✅ Gumroad product created: {product_id}")
return product_id
else:
print(f"❌ Gumroad error: {response.status_code} - {response.text}")
return None

def post_to_twitter(prompt_data: dict, product_url: str) -> bool:
"""X (Twitter) に投稿"""
try:
from twitter import Api

api = Api(
consumer_key=TWITTER_API_KEY,
consumer_secret=TWITTER_API_SECRET,
sleep_on_rate_limit=True
)

tweet_text = f"""
🚀 New prompt dropped: {prompt_data['title']}

Category: {prompt_data['category']}
Price: ${prompt_data['price']}

🔗 Get it now:
{product_url}

#PromptEngineering #AI #ChatGPT
""".strip()

status = api.PostUpdate(tweet_text)
print(f"✅ Tweet posted: {status.id}")
return True
except Exception as e:
print(f"⚠️ Twitter error (non-critical): {e}")
return False

def log_sales_data(prompt_data: dict, product_id: str):
"""売上データをログファイルに記録"""
log_entry = {
"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
"product_id": product_id,
"title": prompt_data["title"],
"category": prompt_data["category"],
"price": prompt_data["price"],
"status": "created"
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

print(f"📊 Sales log updated")

def send_daily_report(prompt_data: dict):
"""日次レポートをメール送信"""
try:
msg = MIMEMultipart()
msg["From"] = GMAIL_USER
msg["To"] = GMAIL_USER
msg["Subject"] = f"PromptFactory Daily Report - {datetime.now().strftime('%Y-%m-%d')}"

body = f"""
PromptFactory Daily Report
========================

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Generated Prompt:
- Title: {prompt_data['title']}
- Category: {prompt_data['category']}
- Price: ${prompt_data['price']}
- Use Case: {prompt_data['use_case']}

Status: ✅ Product created and posted

Next steps:
- Monitor sales performance
- Check X engagement
- Review customer feedback

=========================
Automated by PromptFactory
"""

msg.attach(MIMEText(body, "plain"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
server.login(GMAIL_USER, GMAIL_PASSWORD)
server.send_message(msg)

print("📧 Daily report sent")
except Exception as e:
print(f"⚠️ Email error (non-critical): {e}")

def main():
"""メイン実行フロー"""
print("🚀 PromptFactory Daily Execution Started")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

try:
# 1. ランダムにカテゴリを選択
import random
category = random.choice(CATEGORIES)
print(f"📂 Selected category: {category}")

# 2. プロンプトを生成
print("🤖 Generating prompt with Claude...")
prompt_data = generate_prompt(category)
print(f"✅ Prompt generated: {prompt_data['title']}")

# 3. Gumroad に商品を作成
print("🛒 Creating Gumroad product...")
product_id = create_gumroad_product(prompt_data)

if not product_id:
print("❌ Failed to create product, stopping execution")
return

# 4. X に投稿
product_url = f"https://gumroad.com/l/{product_id}"
print("📱 Posting to X...")
post_to_twitter(prompt_data, product_url)

# 5. ログに記録
print("📊 Logging data...")
log_sales_data(prompt_data, product_id)

# 6. レポートを送信
print("📧 Sending daily report...")
send_daily_report(prompt_data)

print("\n✅ PromptFactory Daily Execution Completed Successfully!")
print(f"📦 Product URL: {product_url}")

except Exception as e:
print(f"\n❌ Error during execution: {e}")
print("Attempting to send error report...")
try:
msg = MIMEMultipart()
msg["From"] = GMAIL_USER
msg["To"] = GMAIL_USER
msg["Subject"] = "⚠️ PromptFactory Error Report"
msg.attach(MIMEText(f"Error: {str(e)}", "plain"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
server.login(GMAIL_USER, GMAIL_PASSWORD)
server.send_message(msg)
except:
pass

if __name__ == "__main__":
main()
```
