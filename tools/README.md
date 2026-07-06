# WorkBuddy 工具客户端

真实工具实现，替代模拟调用。

## 文件

- `web_client.py` — HTTP 请求（requests）
- `browser_client.py` — 浏览器自动化（Playwright）
- `git_client.py` — Git 操作

## 使用示例

```python
from tools.web_client import WebClient
from tools.browser_client import BrowserClient
from tools.git_client import GitClient

# Web
web = WebClient()
resp = web.get("https://api.example.com/data")
print(resp.json_data)

# Browser
with BrowserClient() as browser:
    result = browser.fetch("https://example.com", screenshot=True)
    print(result.title)

# Git
git = GitClient(repo_path=r"C:\Users\lu\.workbuddy")
print(git.log(5).stdout)
```

## 安装依赖

```bash
pip install requests playwright chromadb
playwright install
```
