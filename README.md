
1. 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. 生成新的个人访问令牌
3. 选择所需权限：
   - `repo` - 仓库访问权限
   - `user` - 用户信息权限
   - `delete_repo` - 删除仓库权限（可选）
   
最后在 github_dingtalk_agent.py 文件设置你的github tokens (github_token = "your_github_token")

运行 github_dingtalk_agent.py 即可使用 GitBot Aegnt
