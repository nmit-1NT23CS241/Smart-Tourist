from fastapi.responses import HTMLResponse

@app.get("/documents/{user_id}", response_class=HTMLResponse)
async def get_user_documents(user_id: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SafarAI Digital Travel ID</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .header {{ background: #1A1A2E; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 5px 0 0; color: #aaa; }}
            .card {{ background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .verified {{ color: #2E7D6E; font-weight: bold; font-size: 18px; text-align: center; margin: 20px 0; }}
            .uid {{ color: #999; font-size: 12px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌍 SafarAI</h1>
            <p>Digital Travel ID</p>
        </div>
        <div class="verified">✅ Verified Traveller</div>
        <div class="card">
            <b>Traveller ID</b><br>
            <span style="color:#1A1A2E">ST-{user_id[:8].upper()}</span>
        </div>
        <div class="card">
            <b>Document Vault</b><br>
            <p style="color:#666">This traveller has securely stored their travel documents in SafarAI.</p>
        </div>
        <div class="uid">Powered by SafarAI · nmit-1NT23CS241</div>
    </body>
    </html>
    """
