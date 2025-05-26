import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any

class GitHubClient:
    """GitHub API客户端，用于通过HTTP接口操作GitHub"""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """
        初始化GitHub客户端
        
        Args:
            token: GitHub个人访问令牌
            base_url: GitHub API基础URL
        """
        self.token = token
        self.base_url = base_url
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Python-GitHub-Client'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求到GitHub API
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            data: 请求数据
            
        Returns:
            API响应的JSON数据
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # 准备请求数据
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
            self.headers['Content-Type'] = 'application/json'
        
        # 创建请求
        req = urllib.request.Request(url, data=request_data, headers=self.headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
        except urllib.error.HTTPError as e:
            error_data = e.read().decode('utf-8')
            try:
                error_json = json.loads(error_data)
                raise Exception(f"GitHub API Error {e.code}: {error_json.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP Error {e.code}: {error_data}")
        except urllib.error.URLError as e:
            raise Exception(f"Network Error: {e.reason}")
    
    # 用户相关操作
    def get_user(self, username: Optional[str] = None) -> Dict:
        """获取用户信息"""
        endpoint = f"users/{username}" if username else "user"
        return self._make_request("GET", endpoint)
    
    def get_user_repos(self, username: Optional[str] = None, per_page: int = 30) -> List[Dict]:
        """获取用户的仓库列表"""
        endpoint = f"users/{username}/repos" if username else "user/repos"
        endpoint += f"?per_page={per_page}"
        return self._make_request("GET", endpoint)
    
    # 仓库相关操作
    def get_repo(self, owner: str, repo: str) -> Dict:
        """获取仓库信息"""
        return self._make_request("GET", f"repos/{owner}/{repo}")
    
    def create_repo(self, name: str, description: str = "", private: bool = False) -> Dict:
        """创建新仓库"""
        data = {
            "name": name,
            "description": description,
            "private": private
        }
        return self._make_request("POST", "user/repos", data)
    
    def delete_repo(self, owner: str, repo: str) -> Dict:
        """删除仓库"""
        return self._make_request("DELETE", f"repos/{owner}/{repo}")
    
    def fork_repo(self, owner: str, repo: str) -> Dict:
        """Fork仓库"""
        return self._make_request("POST", f"repos/{owner}/{repo}/forks")
    
    # 文件操作
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Dict:
        """获取文件内容"""
        endpoint = f"repos/{owner}/{repo}/contents/{path}?ref={ref}"
        return self._make_request("GET", endpoint)
    
    def create_file(self, owner: str, repo: str, path: str, content: str, 
                   message: str, branch: str = "main") -> Dict:
        """创建文件"""
        import base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        return self._make_request("PUT", f"repos/{owner}/{repo}/contents/{path}", data)
    
    def update_file(self, owner: str, repo: str, path: str, content: str, 
                   message: str, sha: str, branch: str = "main") -> Dict:
        """更新文件"""
        import base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": message,
            "content": encoded_content,
            "sha": sha,
            "branch": branch
        }
        return self._make_request("PUT", f"repos/{owner}/{repo}/contents/{path}", data)
    
    def delete_file(self, owner: str, repo: str, path: str, message: str, 
                   sha: str, branch: str = "main") -> Dict:
        """删除文件"""
        data = {
            "message": message,
            "sha": sha,
            "branch": branch
        }
        return self._make_request("DELETE", f"repos/{owner}/{repo}/contents/{path}", data)
    
    # Issue相关操作
    def get_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """获取Issues列表"""
        endpoint = f"repos/{owner}/{repo}/issues?state={state}"
        return self._make_request("GET", endpoint)
    
    def create_issue(self, owner: str, repo: str, title: str, body: str = "", 
                    labels: List[str] = None) -> Dict:
        """创建Issue"""
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
        return self._make_request("POST", f"repos/{owner}/{repo}/issues", data)
    
    def update_issue(self, owner: str, repo: str, issue_number: int, 
                    title: str = None, body: str = None, state: str = None) -> Dict:
        """更新Issue"""
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        
        return self._make_request("PATCH", f"repos/{owner}/{repo}/issues/{issue_number}", data)
    
    # Pull Request相关操作
    def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """获取Pull Requests列表"""
        endpoint = f"repos/{owner}/{repo}/pulls?state={state}"
        return self._make_request("GET", endpoint)
    
    def create_pull_request(self, owner: str, repo: str, title: str, head: str, 
                           base: str, body: str = "") -> Dict:
        """创建Pull Request"""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        return self._make_request("POST", f"repos/{owner}/{repo}/pulls", data)
    
    # 分支操作
    def get_branches(self, owner: str, repo: str) -> List[Dict]:
        """获取分支列表"""
        return self._make_request("GET", f"repos/{owner}/{repo}/branches")
    
    def create_branch(self, owner: str, repo: str, branch_name: str, sha: str) -> Dict:
        """创建分支"""
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        return self._make_request("POST", f"repos/{owner}/{repo}/git/refs", data)
    
    # 搜索功能
    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc") -> Dict:
        """搜索仓库"""
        encoded_query = urllib.parse.quote(query)
        endpoint = f"search/repositories?q={encoded_query}&sort={sort}&order={order}"
        return self._make_request("GET", endpoint)
    
    def search_users(self, query: str) -> Dict:
        """搜索用户"""
        encoded_query = urllib.parse.quote(query)
        endpoint = f"search/users?q={encoded_query}"
        return self._make_request("GET", endpoint)


def main():
    """示例用法"""
    # 注意：请替换为你的GitHub个人访问令牌
    TOKEN = "your_github_token_here"
    
    if TOKEN == "your_github_token_here":
        print("请先设置你的GitHub个人访问令牌！")
        print("1. 访问 https://github.com/settings/tokens")
        print("2. 生成新的个人访问令牌")
        print("3. 将令牌替换到代码中的TOKEN变量")
        return
    
    # 创建GitHub客户端
    client = GitHubClient(TOKEN)
    
    try:
        # 获取当前用户信息
        print("=== 获取用户信息 ===")
        user = client.get_user()
        print(f"用户名: {user['login']}")
        print(f"姓名: {user.get('name', 'N/A')}")
        print(f"公开仓库数: {user['public_repos']}")
        
        # 获取用户仓库
        print("\n=== 获取仓库列表 ===")
        repos = client.get_user_repos(per_page=5)
        for repo in repos[:3]:  # 只显示前3个
            print(f"- {repo['name']}: {repo.get('description', 'No description')}")
        
        # 搜索仓库
        print("\n=== 搜索Python相关仓库 ===")
        search_result = client.search_repositories("python machine learning", sort="stars")
        for repo in search_result['items'][:3]:  # 只显示前3个
            print(f"- {repo['full_name']}: ⭐{repo['stargazers_count']}")
        
        print("\n操作完成！")
        
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
