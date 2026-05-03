import urllib.request, urllib.parse, http.cookiejar, re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

resp = opener.open(urllib.request.Request('http://127.0.0.1:5000/admin/login'))
html = resp.read().decode('utf-8')
csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
token = csrf.group(1) if csrf else ''

data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123', 'csrf_token': token}).encode()
resp = opener.open(urllib.request.Request('http://127.0.0.1:5000/admin/login', data=data))
print('Login:', resp.getcode())

resp = opener.open(urllib.request.Request('http://127.0.0.1:5000/admin/match/config'))
html = resp.read().decode('utf-8')
print('Match config page:', resp.getcode())
print('Has rematch button:', 'rematchAll' in html)

csrf2 = re.search(r"var csrfToken = '([^']+)'", html)
token2 = csrf2.group(1) if csrf2 else ''
print('CSRF token found:', bool(token2))

req = urllib.request.Request('http://127.0.0.1:5000/admin/match/rematch-all',
    data=b'{}',
    headers={'Content-Type': 'application/json', 'X-CSRFToken': token2})
try:
    resp = opener.open(req)
    result = resp.read().decode('utf-8')
    print('Rematch result:', result)
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print('Rematch error:', e.code, body[:200])
