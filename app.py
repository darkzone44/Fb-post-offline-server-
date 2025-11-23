from flask import Flask, request, render_template_string
import requests
import re

app = Flask(__name__)
app.debug = True

headers_template = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
}

def extract_access_token(cookie):
    """Facebook mobile page se access_token scrape karna"""
    headers = headers_template.copy()
    headers['Cookie'] = cookie

    url = "https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed"
    # Ye URL Facebook page hota hai jahan se access token mil sakta hai (thoda hacky method)
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None, "Failed to fetch page, possibly invalid cookie"

    # Facebook JSON responses me token ko "accessToken":"...token..." form me rakh sakta hai
    token_match = re.search(r'"accessToken":"(EAAw+)"', r.text)
    if token_match:
        return token_match.group(1), None
    else:
        return None, "Access token not found in response"

PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Facebook Access Token Extractor</title>
  <style>
    body { font-family: Arial, sans-serif; background: #222; color: #eee; padding: 2rem; }
    .container { max-width: 600px; margin: auto; background: #333; padding: 20px; border-radius: 10px; }
    textarea, input[type=text], button { width: 100%; padding: 10px; margin-top: 10px; border-radius: 5px; border: none; }
    textarea { height: 120px; font-family: monospace; }
    button { background: #007bff; color: white; font-weight: bold; cursor: pointer; }
    button:hover { background: #0056b3; }
    .result { background: #111; padding: 10px; margin-top: 20px; border-radius: 5px; word-wrap: break-word; }
    label { font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Facebook Access Token Extractor</h2>
    <form method="post">
      <label>Paste Full Facebook Cookie Here:</label>
      <textarea name="cookie" placeholder="m_pixel_ratio=1.4...etc" required></textarea>
      <button type="submit">Extract Access Token</button>
    </form>

    {% if token %}
    <div class="result">
      <strong>Extracted Access Token:</strong><br />
      <code>{{ token }}</code>
    </div>
    {% endif %}

    {% if error %}
    <div class="result" style="color: #ff5555;">
      <strong>Error:</strong><br />
      {{ error }}
    </div>
    {% endif %}
  </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    token = None
    error = None
    if request.method == 'POST':
        cookie = request.form.get('cookie')
        if cookie:
            token, error = extract_access_token(cookie.strip())
    return render_template_string(PAGE_HTML, token=token, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5040)
