"""
演示辅助工具模块

提供常用的辅助函数和类，用于简化演示脚本的编写
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx


class DemoLogger:
    """演示日志记录器"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.logs = []
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        
        if self.verbose:
            print(log_entry)
    
    def step(self, step_num: int, message: str):
        """记录步骤"""
        self.log(f"{'='*60}", "STEP")
        self.log(f"步骤 {step_num}: {message}", "STEP")
        self.log(f"{'='*60}", "STEP")
    
    def success(self, message: str):
        """记录成功"""
        self.log(f"[OK] {message}", "SUCCESS")
    
    def error(self, message: str):
        """记录错误"""
        self.log(f"[ERROR] {message}", "ERROR")
    
    def warning(self, message: str):
        """记录警告"""
        self.log(f"[WARNING] {message}", "WARNING")
    
    def info(self, message: str):
        """记录信息"""
        self.log(f"[INFO] {message}", "INFO")
    
    def save_to_file(self, filepath: str):
        """保存日志到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.logs))


class APIClient:
    """简化的 API 客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout  # httpx 接受数字作为超时
        self.token: Optional[str] = None
        self.api_key: Optional[str] = None
    
    def set_token(self, token: str):
        """设置 JWT Token"""
        self.token = token
    
    def set_api_key(self, api_key: str):
        """设置 API Key"""
        self.api_key = api_key
    
    def _get_headers(self, has_files: bool = False) -> Dict[str, str]:
        """获取请求头"""
        headers = {}
        
        # 如果有文件上传，不设置 Content-Type，让 httpx 自动处理
        if not has_files:
            headers["Content-Type"] = "application/json"
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        json: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self._get_headers(has_files=bool(files)),
                    json=json,
                    files=files,
                    params=params
                )
                
                if response.status_code >= 400:
                    raise Exception(f"API Error: {response.status_code} - {response.text}")
                
                return response.json()
            
            except httpx.TimeoutException:
                raise Exception(f"Request timeout after {self.timeout}s")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET 请求"""
        return await self.request("GET", endpoint, params=params)
    
    async def post(
        self, 
        endpoint: str, 
        json: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """POST 请求"""
        return await self.request("POST", endpoint, json=json, files=files)
    
    async def put(self, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """PUT 请求"""
        return await self.request("PUT", endpoint, json=json)
    
    async def delete(self, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        """DELETE 请求"""
        return await self.request("DELETE", endpoint, json=json)


def format_time(seconds: float) -> str:
    """格式化时间为可读字符串"""
    if seconds < 1:
        return f"{seconds:.2f}秒"
    elif seconds < 60:
        return f"{seconds:.1f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.1f}秒"


def print_section(title: str, char: str = "="):
    """打印分隔线"""
    print(f"\n{char * 70}")
    print(f"  {title}")
    print(f"{char * 70}\n")


def print_result(label: str, value: Any, indent: int = 0):
    """打印结果"""
    prefix = "  " * indent
    print(f"{prefix}{label}: {value}")


async def wait_for_processing(
    func, 
    timeout: int = 300, 
    interval: int = 5,
    status_endpoint: str = None,
    client: APIClient = None
):
    """等待处理完成"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = await func()
        
        if result:
            return result
        
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Processing timed out after {timeout} seconds")


def create_demo_user(email: str, password: str, name: str) -> Dict[str, str]:
    """创建演示用户数据结构"""
    return {
        "email": email,
        "password": password,
        "name": name
    }


def create_demo_kb(name: str, description: str, storage_config: Optional[Dict] = None) -> Dict[str, Any]:
    """创建演示知识库数据结构"""
    kb_data = {
        "name": name,
        "description": description
    }
    
    if storage_config:
        kb_data["storage_config"] = storage_config
    
    return kb_data


# 颜色输出（Windows 终端支持）
class Colors:
    """ANSI 颜色代码"""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    
    @classmethod
    def disable(cls):
        """禁用颜色（Windows 兼容）"""
        cls.RESET = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""


def colorize(text: str, color: str) -> str:
    """给文本添加颜色"""
    return f"{color}{text}{Colors.RESET}"


# 演示数据清理助手
class DemoCleanupHelper:
    """演示数据清理助手"""
    
    def __init__(self, client: APIClient, logger: DemoLogger):
        self.client = client
        self.logger = logger
        self.created_users = []
        self.created_kbs = []
    
    def add_user(self, user_id: str):
        """记录创建的用户"""
        self.created_users.append(user_id)
    
    def add_kb(self, kb_id: str):
        """记录创建的知识库"""
        self.created_kbs.append(kb_id)
    
    async def cleanup_all(self):
        """清理所有演示数据"""
        self.logger.step(0, "清理演示数据")
        
        # 删除知识库
        for kb_id in self.created_kbs:
            try:
                await self.client.delete(f"/api/v1/knowledge-bases/{kb_id}")
                self.logger.success(f"已删除知识库：{kb_id}")
            except Exception as e:
                self.logger.error(f"删除知识库失败 {kb_id}: {str(e)}")
        
        # 删除用户（需要管理员权限）
        # 注意：当前 API 可能不支持删除用户，这里预留接口
        self.logger.info(f"待删除用户列表：{self.created_users}")
        
        self.logger.success("演示数据清理完成")
