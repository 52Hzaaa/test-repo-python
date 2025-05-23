# 测试仓库

这是通过GitHub API创建的测试仓库。

## 功能特性

- 通过Python HTTP请求操作GitHub
- 支持仓库、文件、Issue等操作
- 简单易用的API封装

## 使用方法

```python
from github_client import GitHubClient

client = GitHubClient("your_token")
user = client.get_user()
print(user['login'])
```
