import urllib.request, urllib.parse, http.cookiejar, re

base = 'http://127.0.0.1:5000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

resp = opener.open(urllib.request.Request(base + '/login'))
html = resp.read().decode('utf-8')

csrf = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
if not csrf:
    csrf = re.search(r'value="([^"]+)"\s+name="csrf_token"', html)
if not csrf:
    csrf = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', html)
token = csrf.group(1) if csrf else ''
print(f'CSRF token: {token[:20]}...' if token else 'No CSRF token found')

data = urllib.parse.urlencode({'username': '张三', 'password': '123456', 'csrf_token': token}).encode()
try:
    resp = opener.open(urllib.request.Request(base + '/login', data=data))
    print(f'Login OK: {resp.getcode()} URL: {resp.url[:80]}')
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f'Login error: {e.code}')
    if 'csrf' in body.lower():
        print('CSRF validation failed')
    if '用户名' in body or '密码' in body:
        print('Login form shown again (wrong credentials)')

resp = opener.open(urllib.request.Request(base + '/match/list'))
html = resp.read().decode('utf-8')
has_match = 'match-card' in html or '匹配' in html
print(f'Match page: has_match={has_match}, length={len(html)}')

resp = opener.open(urllib.request.Request(base + '/chat/list'))
html = resp.read().decode('utf-8')
has_chat = '消息中心' in html or 'chat-card' in html or '暂无消息' in html
print(f'Chat page: has_chat={has_chat}')

resp = opener.open(urllib.request.Request(base + '/lost/create'))
html = resp.read().decode('utf-8')
has_cats = '请选择分类' in html and ('电子产品' in html or '证件' in html)
print(f'Create lost: has_categories={has_cats}')

resp = opener.open(urllib.request.Request(base + '/found/create'))
html = resp.read().decode('utf-8')
has_cats = '请选择分类' in html and ('电子产品' in html or '证件' in html)
print(f'Create found: has_categories={has_cats}')
