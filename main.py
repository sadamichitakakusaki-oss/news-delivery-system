import os
import smtplib
import ssl
import requests
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ===== 設定 =====
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_HOST = "mail1002.onamae.ne.jp"
SMTP_PORT = 465
TO_EMAIL = "taka.s@sintronix.jp"

# ===== ニュース収集 =====
def get_news(query, max_articles=5):
    """NewsAPIで最新ニュースを取得"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "from": yesterday,
        "sortBy": "publishedAt",
        "language": "jp",
        "apiKey": NEWS_API_KEY,
        "pageSize": max_articles,
    }
    # 日本語ニュースが少ない場合は英語も検索
    response = requests.get(url, params=params)
    data = response.json()
    articles = data.get("articles", [])

    if len(articles) < 3:
        params["language"] = "en"
        response = requests.get(url, params=params)
        data = response.json()
        articles = data.get("articles", [])

    return articles

# ===== HTMLメール生成 =====
def build_html(categories):
    """HTMLメールを生成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    html = f"""
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
        .container {{ max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 12px; line-height: 1.6; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ margin-top: 30px; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 10px; }}
        .no-news {{ color: #999; font-style: italic; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>📰 半導体・部材 最新ニュース</h1>
        <p>{today} 配信</p>
    """

    for category_name, articles in categories.items():
        html += f"<h2>📌 {category_name}</h2><ul>"
        if articles:
            for article in articles:
                title = article.get("title", "タイトルなし")
                url = article.get("url", "#")
                source = article.get("source", {}).get("name", "不明")
                published = article.get("publishedAt", "")[:10]
                description = article.get("description", "") or ""
                if len(description) > 100:
                    description = description[:100] + "..."
                html += f"""
                <li>
                  <a href="{url}" target="_blank"><strong>{title}</strong></a><br>
                  <small>📅 {published} ｜ 🔍 {source}</small><br>
                  <small>{description}</small>
                </li>
                """
        else:
            html += '<li class="no-news">本日の新着ニュースはありませんでした。</li>'
        html += "</ul>"

    html += """
        <div class="footer">
          このメールは自動配信システムにより送信されています。
        </div>
      </div>
    </body>
    </html>
    """
    return html

# ===== メール送信 =====
def send_email(html_content):
    """SMTPでメール送信"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【半導体ニュース】{datetime.now().strftime('%Y/%m/%d')} 最新情報"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
    print(f"✅ メール送信完了：{TO_EMAIL}")

# ===== メイン処理 =====
def main():
    print(f"🚀 ニュース配信開始：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    categories = {
        "AI半導体とその周辺部材": get_news("AI半導体 OR AI semiconductor OR NVIDIA GPU AI chip"),
        "パワー半導体とその周辺部材": get_news("パワー半導体 OR power semiconductor OR SiC GaN inverter"),
        "セラミックス基板とその周辺部材": get_news("セラミックス基板 OR ceramic substrate OR LTCC HTCC alumina"),
    }

    html = build_html(categories)
    send_email(html)
    print("✅ 配信完了")

if __name__ == "__main__":
    main()
