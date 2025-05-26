#!/usr/bin/env python
import json
import logging
from dingtalk_stream import AckMessage
import dingtalk_stream
from urllib.parse import unquote, urlparse, parse_qs
from github_client import GitHubClient

class GitHubHandler(dingtalk_stream.GraphHandler):
    def __init__(self, github_token: str, logger: logging.Logger = None):
        super(dingtalk_stream.GraphHandler, self).__init__()
        self.github_client = GitHubClient(github_token)
        self.logger = logger or logging.getLogger(__name__)

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        request = dingtalk_stream.GraphRequest.from_dict(callback.data)
        
        decode_uri = unquote(request.request_line.uri)
        parsed_url = urlparse(decode_uri)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        print(f"Processing request: {decode_uri}")
        
        response = dingtalk_stream.GraphResponse()
        response.status_line.code = 200
        response.status_line.reason_phrase = 'OK'
        response.headers['Content-Type'] = 'application/json'
        
        try:
            # 用户相关操作
            if path == "/user":
                result = await self._get_current_user()
            elif path.startswith("/users/"):
                username = path.split("/users/")[1]
                result = await self._get_user(username)
            elif path == "/user/repos":
                per_page = int(query_params.get('per_page', [30])[0])
                result = await self._get_user_repos(per_page)
            
            # 仓库相关操作
            elif path.startswith("/repos/") and path.count("/") == 3:
                parts = path.split("/")
                owner, repo = parts[2], parts[3]
                if request.request_line.method == "GET":
                    result = await self._get_repo(owner, repo)
                elif request.request_line.method == "DELETE":
                    result = await self._delete_repo(owner, repo)
            
            # 文件操作
            elif "/contents/" in path:
                parts = path.split("/")
                owner, repo = parts[2], parts[3]
                file_path = "/".join(parts[5:])  # contents后面的路径
                
                if request.request_line.method == "GET":
                    ref = query_params.get('ref', ['main'])[0]
                    result = await self._get_file_content(owner, repo, file_path, ref)
                elif request.request_line.method == "PUT":
                    body_data = json.loads(request.body) if request.body else {}
                    result = await self._create_or_update_file(owner, repo, file_path, body_data)
            
            # Issues操作
            elif path.endswith("/issues"):
                parts = path.split("/")
                owner, repo = parts[2], parts[3]
                
                if request.request_line.method == "GET":
                    state = query_params.get('state', ['open'])[0]
                    result = await self._get_issues(owner, repo, state)
                elif request.request_line.method == "POST":
                    body_data = json.loads(request.body) if request.body else {}
                    result = await self._create_issue(owner, repo, body_data)
            
            elif "/issues/" in path and path.count("/") == 5:
                parts = path.split("/")
                owner, repo, issue_number = parts[2], parts[3], int(parts[5])
                
                if request.request_line.method == "PATCH":
                    body_data = json.loads(request.body) if request.body else {}
                    result = await self._update_issue(owner, repo, issue_number, body_data)
            
            # 搜索操作
            elif path == "/search/repositories":
                q = query_params.get('q', [''])[0]
                sort = query_params.get('sort', [''])[0]
                order = query_params.get('order', ['desc'])[0]
                result = await self._search_repositories(q, sort, order)
            
            elif path == "/search/users":
                q = query_params.get('q', [''])[0]
                sort = query_params.get('sort', [''])[0]
                order = query_params.get('order', ['desc'])[0]
                result = await self._search_users(q, sort, order)
            
            # Fork操作
            elif path.endswith("/forks"):
                parts = path.split("/")
                owner, repo = parts[2], parts[3]
                result = await self._fork_repo(owner, repo)
            
            # 分支操作
            elif path.endswith("/branches"):
                parts = path.split("/")
                owner, repo = parts[2], parts[3]
                result = await self._get_branches(owner, repo)
            
            # 创建仓库
            elif path == "/user/repos" and request.request_line.method == "POST":
                body_data = json.loads(request.body) if request.body else {}
                result = await self._create_repo(body_data)
            
            else:
                result = {"error": "Endpoint not found", "path": path}
                response.status_line.code = 404
                response.status_line.reason_phrase = 'Not Found'
            
            response.body = json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            response.status_line.code = 500
            response.status_line.reason_phrase = 'Internal Server Error'
            response.body = json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }, ensure_ascii=False)
        
        return AckMessage.STATUS_OK, response.to_dict()
    
    # 用户相关方法
    async def _get_current_user(self):
        """获取当前用户信息"""
        return self.github_client.get_user()
    
    async def _get_user(self, username: str):
        """获取指定用户信息"""
        return self.github_client.get_user(username)
    
    async def _get_user_repos(self, per_page: int = 30):
        """获取用户仓库列表"""
        return self.github_client.get_user_repos(per_page=per_page)
    
    # 仓库相关方法
    async def _get_repo(self, owner: str, repo: str):
        """获取仓库信息"""
        return self.github_client.get_repo(owner, repo)
    
    async def _create_repo(self, data: dict):
        """创建仓库"""
        name = data.get('name')
        description = data.get('description', '')
        private = data.get('private', False)
        return self.github_client.create_repo(name, description, private)
    
    async def _delete_repo(self, owner: str, repo: str):
        """删除仓库"""
        return self.github_client.delete_repo(owner, repo)
    
    async def _fork_repo(self, owner: str, repo: str):
        """Fork仓库"""
        return self.github_client.fork_repo(owner, repo)
    
    # 文件相关方法
    async def _get_file_content(self, owner: str, repo: str, path: str, ref: str = "main"):
        """获取文件内容"""
        return self.github_client.get_file_content(owner, repo, path, ref)
    
    async def _create_or_update_file(self, owner: str, repo: str, path: str, data: dict):
        """创建或更新文件"""
        import base64
        
        content = base64.b64decode(data['content']).decode('utf-8')
        message = data['message']
        branch = data.get('branch', 'main')
        sha = data.get('sha')
        
        if sha:
            # 更新文件
            return self.github_client.update_file(owner, repo, path, content, message, sha, branch)
        else:
            # 创建文件
            return self.github_client.create_file(owner, repo, path, content, message, branch)
    
    # Issues相关方法
    async def _get_issues(self, owner: str, repo: str, state: str = "open"):
        """获取Issues列表"""
        return self.github_client.get_issues(owner, repo, state)
    
    async def _create_issue(self, owner: str, repo: str, data: dict):
        """创建Issue"""
        title = data['title']
        body = data.get('body', '')
        labels = data.get('labels', [])
        return self.github_client.create_issue(owner, repo, title, body, labels)
    
    async def _update_issue(self, owner: str, repo: str, issue_number: int, data: dict):
        """更新Issue"""
        title = data.get('title')
        body = data.get('body')
        state = data.get('state')
        return self.github_client.update_issue(owner, repo, issue_number, title, body, state)
    
    # 搜索相关方法
    async def _search_repositories(self, query: str, sort: str = "", order: str = "desc"):
        """搜索仓库"""
        return self.github_client.search_repositories(query, sort, order)
    
    async def _search_users(self, query: str, sort: str = "", order: str = "desc"):
        """搜索用户"""
        return self.github_client.search_users(query)
    
    # 分支相关方法
    async def _get_branches(self, owner: str, repo: str):
        """获取分支列表"""
        return self.github_client.get_branches(owner, repo)


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # 钉钉AI Agent配置
    client_id = "ding2v0uv1yb4ruamecv"
    client_secret = "3N_SIE_ZFbhF4iCHy7825d3y6yr4NTuiKlGYF9p7fG5oP0hQPW4o83e4tKNbF169"
    
    # GitHub配置 这里输入你的 github toekn
    github_token = "your_github_token"
    
    if client_id == "your_ai_agent_id" or github_token == "your_github_token":
        logger.error("请先配置钉钉AI Agent和GitHub令牌！")
        print("配置步骤：")
        print("1. 设置钉钉AI Agent的client_id和client_secret")
        print("2. 设置GitHub个人访问令牌")
        return
    
    try:
        # 创建钉钉Stream客户端
        credential = dingtalk_stream.Credential(client_id, client_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential)
        
        # 注册GitHub处理器
        handler = GitHubHandler(github_token, logger)
        client.register_callback_handler(dingtalk_stream.graph.GraphMessage.TOPIC, handler)
        
        logger.info("GitHub钉钉AI Agent启动成功！")
        logger.info("支持的GitHub API操作：")
        logger.info("- 用户信息查询: GET /user, /users/{username}")
        logger.info("- 仓库管理: GET/POST/DELETE /repos/{owner}/{repo}")
        logger.info("- 文件操作: GET/PUT /repos/{owner}/{repo}/contents/{path}")
        logger.info("- Issues管理: GET/POST/PATCH /repos/{owner}/{repo}/issues")
        logger.info("- 搜索功能: GET /search/repositories, /search/users")
        logger.info("- 其他功能: Fork仓库, 分支管理等")
        
        # 启动服务
        client.start_forever()
        
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")


if __name__ == '__main__':
    main()
