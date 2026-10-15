#!/usr/bin/env python3
"""PromptFactory: daily prompt generation -> X post -> email report.

Phase 1: Claude writes a short, useful prompt for one of three audiences,
posts it to X with a link to the Gumroad store, and emails a short report.
Each step logs clearly so GitHub Actions logs show what failed.
"""
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import anthropic
import requests
import tweepy

JST = timezone(timedelta(hours=9))


def env(name, default=None):
    """Read a secret and drop any spaces/newlines picked up when pasting.

    API keys, tokens and Gmail app passwords never contain whitespace, so
    removing all of it is safe and fixes copy-paste line breaks.
    """
    value = "".join((os.getenv(name) or "").split())
    return value or default


CLAUDE_API_KEY = env("CLAUDE_API_KEY")
CLAUDE_MODEL = env("CLAUDE_MODEL", "claude-haiku-5-5")
GUMROAD_TOKEN = env("GUMROAD_TOKEN")
GMAIL_USER = env("GMAIL_USER")
GMAIL_PASSWORD = env("GMAIL_PASSWORD")
REPORT_TO = env("REPORT_TO") or GMAIL_USER
DRY_RUN = (env("DRY_RUN", "false")).lower() == "true"

# Rotate the three audiences by date so each gets equal exposure.
CATEGORIES = [
    ("marketing", "マーケティング・営業担当者"),
    ("entrepreneur", "起業家・スモールビジネスオーナー"),
    ("developer", "個人開発者"),
]


def check_secrets():
    """Log the shape of each secret (never its value) to diagnose setup issues."""
    for name in ["CLAUDE_API_KEY", "GUMROAD_TOKEN", "GMAIL_USER", "GMAIL_PASSWORD",
                 "TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET",
                 "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"]:
        v = env(name, "")
        notes = []
        if not v:
            notes.append("EMPTY")
        if v and not v.isascii():
            notes.append("NON-ASCII CHARACTERS")
        if any(c.isspace() for c in (os.getenv(name) or "").strip()):
            notes.append("had spaces/newlines (auto-removed)")
        if name == "CLAUDE_API_KEY" and v and not v.startswith("sk-ant-"):
            notes.append("does not start with sk-ant-")
        print(f"[check] {name}: length={len(v)} {'OK' if not notes else ' / '.join(notes)}")
        if notes:
            print(f"::notice title=Secret check::{name}: {' / '.join(notes)}")


def pick_category(today):
    return CATEGORIES[today.toordinal() % len(CATEGORIES)]


def get_store_url():
    """Return the URL of a published Gumroad product, if any."""
    if not GUMROAD_TOKEN:
        print("[gumroad] GUMROAD_TOKEN not set; posting without a link")
        return None
    try:
        r = requests.get(
            "https://api.gumroad.com/v2/products",
            params={"access_token": GUMROAD_TOKEN},
            timeout=20,
        )
        r.raise_for_status()
        products = [p for p in r.json().get("products", []) if p.get("published")]
        if not products:
            print("[gumroad] no published products found")
            return None
        url = products[0].get("short_url")
        print(f"[gumroad] linking to: {products[0].get('name')} ({url})")
        return url
    except Exception as e:  # keep posting even if Gumroad is unreachable
        print(f"[gumroad] error: {e}")
        print(f"::warning title=Gumroad::{str(e).split('?')[0][:300]}")
        return None


def generate_post(audience, has_link):
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    limit = "本文は全角120文字以内" if has_link else "本文は全角135文字以内"
    instruction = f"""あなたは「PromptFactory」というAIプロンプト販売ブランドのSNS担当です。
{audience}向けに、そのまま使えるChatGPT/Claude用プロンプトを1つ考え、Xに投稿する文章を書いてください。

条件:
- 1行目は読者の悩みに刺さる短いフック
- プロンプト本体をそのまま使える形で載せる（[ ]で差し替え箇所を示す）
- 最後に「#PromptFactory」と、関連するハッシュタグを1つ
- {limit}（Xの文字数制限のため厳守）
- 投稿文だけを出力し、前置きや説明は書かない"""
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": instruction}],
    )
    # Newer models may return thinking blocks first; keep only the text.
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise RuntimeError(f"Claude returned no text (stop_reason={response.stop_reason})")
    return text.strip()


def post_to_x(text):
    client = tweepy.Client(
        consumer_key=env("TWITTER_CONSUMER_KEY"),
        consumer_secret=env("TWITTER_CONSUMER_SECRET"),
        access_token=env("TWITTER_ACCESS_TOKEN"),
        access_token_secret=env("TWITTER_ACCESS_TOKEN_SECRET"),
    )
    resp = client.create_tweet(text=text)
    tweet_id = resp.data["id"]
    print(f"[x] posted: https://x.com/i/web/status/{tweet_id}")
    return tweet_id


def send_report(subject, body):
    if not (GMAIL_USER and GMAIL_PASSWORD):
        print("[mail] GMAIL_USER or GMAIL_PASSWORD not set; skipping report")
        print("::warning title=Mail::GMAIL_USER or GMAIL_PASSWORD not set")
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = REPORT_TO
    errors = []
    for mode in ("starttls", "ssl"):
        try:
            if mode == "ssl":
                server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
            else:
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
                server.ehlo()
                server.starttls()
                server.ehlo()
            with server:
                server.login(GMAIL_USER, GMAIL_PASSWORD)
                server.send_message(msg)
            print(f"[mail] report sent via {mode}")
            print(f"::notice title=Mail::report sent via {mode}")
            return
        except Exception as e:
            errors.append(f"{mode}: {type(e).__name__}: {str(e)[:200]}")
            print(f"[mail] {mode} failed: {e}")
    print(f"::warning title=Mail failed::{' || '.join(errors)}")


def main():
    now = datetime.now(JST)
    key, audience = pick_category(now.date())
    print(f"PromptFactory started {now:%Y-%m-%d %H:%M} JST / category={key}")
    check_secrets()

    store_url = get_store_url()
    text = generate_post(audience, has_link=bool(store_url))
    if store_url:
        text = f"{text}\n\n{store_url}"
    print("----- post -----\n" + text + "\n----------------")
    print("::notice title=Post text::" + text.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### PromptFactory {now:%Y-%m-%d %H:%M} JST ({audience})\n\n```\n{text}\n```\n")

    status, tweet_id, error = "OK", None, ""
    if DRY_RUN:
        status = "DRY RUN (not posted)"
    else:
        try:
            tweet_id = post_to_x(text)
        except Exception as e:
            status, error = "FAILED", repr(e)
            print(f"[x] error: {error}")
            print(f"::error title=X post failed::{error[:900]}")

    body = (
        f"日時: {now:%Y-%m-%d %H:%M} JST\n"
        f"カテゴリ: {audience}\n"
        f"結果: {status}\n"
        + (f"投稿: https://x.com/i/web/status/{tweet_id}\n" if tweet_id else "")
        + (f"エラー: {error}\n" if error else "")
        + f"\n--- 投稿文 ---\n{text}\n"
    )
    send_report(f"[PromptFactory] 日報 {now:%m/%d} {status}", body)

    if status == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        # Surface the error as a GitHub annotation (readable via the API).
        msg = f"{type(e).__name__}: {e}"
        cause = e.__cause__ or e.__context__
        if cause:
            msg += f" | cause: {type(cause).__name__}: {cause}"
        print(f"::error title=PromptFactory failed::{msg[:900]}")
        raise
