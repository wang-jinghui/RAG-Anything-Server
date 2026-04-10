"""
演示脚本配置文件

说明：本配置文件会自动从项目根目录的 .env 文件加载配置
      无需手动填写，只需确保 .env 文件已正确配置

使用方法:
    1. 确保项目根目录的 .env 文件已正确配置
    2. 复制此文件为 demo_config.py（可选，如需自定义）
    3. 直接运行演示脚本即可
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 自动加载项目根目录的 .env 文件
ROOT_DIR = Path(__file__).parent.parent
env_path = ROOT_DIR / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"⚠️  警告：未找到 .env 文件：{env_path}")
    print("请确保项目根目录的 .env 文件已正确配置")

# ==================== 服务器配置 ====================
SERVER_HOST = os.getenv("SERVER_HOST", "http://localhost:8000")
API_PREFIX = "/api/v1"

# ==================== 数据库配置 ====================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "raganything")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# ==================== Neo4j 配置 ====================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# ==================== LLM 配置 ====================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:1.7b")
LLM_BINDING_HOST = os.getenv("LLM_BINDING_HOST", "http://localhost:11434")

# ==================== Embedding 配置 ====================
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1024"))

# ==================== Ollama 配置 ====================
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_ENDPOINT = f"{OLLAMA_BASE_URL}/api/embeddings"

# ==================== LightRAG 配置 ====================
LIGHTRAG_KV_STORAGE = os.getenv("LIGHTRAG_KV_STORAGE", "PGKVStorage")
LIGHTRAG_VECTOR_STORAGE = os.getenv("LIGHTRAG_VECTOR_STORAGE", "PGVectorStorage")
LIGHTRAG_GRAPH_STORAGE = os.getenv("LIGHTRAG_GRAPH_STORAGE", "Neo4JStorage")
LIGHTRAG_WORKSPACE = os.getenv("LIGHTRAG_WORKSPACE", "default")

# ==================== 演示文档路径 ====================
# 准备一些测试文档用于演示
DEMO_DOCS_DIR = ROOT_DIR / "demo_documents"
DOCUMENT_FILES = [
    str(ROOT_DIR / "test.pdf"),
    str(ROOT_DIR / "README.md"),
    str(DEMO_DOCS_DIR / "sample_doc.txt"),
]

# ==================== 查询测试配置 ====================
# 测试查询示例
TEST_QUERIES = {
    "naive": "What is the main topic?",
    "local": "Who are the key entities mentioned?",
    "global": "How does this relate to other concepts?",
}

# ==================== API Key 配置 ====================
API_KEY_NAME = "Demo API Key"
API_KEY_DESCRIPTION = "API key for demonstration purposes"

# ==================== 演示模式配置 ====================
# True: 演示模式，会打印详细的步骤说明
# False: 静默模式，只输出关键信息
VERBOSE_MODE = os.getenv("DEMO_VERBOSE", "True").lower() == "true"

# True: 演示结束后自动清理数据
# False: 保留演示数据供后续检查
AUTO_CLEANUP = os.getenv("DEMO_AUTO_CLEANUP", "False").lower() == "false"

# ==================== 超时配置 ====================
# HTTP 请求超时（秒）
HTTP_TIMEOUT = int(os.getenv("DEMO_HTTP_TIMEOUT", "120"))  # Increased for VLM queries

# 文档处理超时（秒）
PROCESSING_TIMEOUT = int(os.getenv("DEMO_PROCESSING_TIMEOUT", "300"))

# 查询超时（秒）
QUERY_TIMEOUT = int(os.getenv("DEMO_QUERY_TIMEOUT", "60"))

# ==================== 重试配置 ====================
# 最大重试次数
MAX_RETRIES = int(os.getenv("DEMO_MAX_RETRIES", "3"))

# 重试延迟（秒）
RETRY_DELAY = int(os.getenv("DEMO_RETRY_DELAY", "2"))

# ==================== 其他配置 ====================
# 是否显示 SQL 日志
SHOW_SQL_LOGS = os.getenv("DEMO_SHOW_SQL_LOGS", "False").lower() == "true"

# 是否显示 LightRAG 内部日志
SHOW_LIGHTRAG_LOGS = os.getenv("DEMO_SHOW_LIGHTRAG_LOGS", "False").lower() == "true"

# 是否保存演示日志
SAVE_DEMO_LOG = os.getenv("DEMO_SAVE_DEMO_LOG", "True").lower() == "true"

# 日志文件路径
DEMO_LOG_PATH = str(ROOT_DIR / "demo_output.log")

# ==================== 演示用户配置（可自定义） ====================
# 这些配置不会从 .env 加载，因为是演示专用的临时用户
# 用户 A (Alice)
USER_A_EMAIL = os.getenv("DEMO_USER_A_EMAIL", "alice.demo@example.com")
USER_A_PASSWORD = os.getenv("DEMO_USER_A_PASSWORD", "DemoPassword123!")
USER_A_NAME = os.getenv("DEMO_USER_A_NAME", "Alice Researcher")

# 用户 B (Bob)
USER_B_EMAIL = os.getenv("DEMO_USER_B_EMAIL", "bob.demo@example.com")
USER_B_PASSWORD = os.getenv("DEMO_USER_B_PASSWORD", "DemoPassword456!")
USER_B_NAME = os.getenv("DEMO_USER_B_NAME", "Bob Student")

# 管理员（可选，如果需要）
ADMIN_EMAIL = os.getenv("DEMO_ADMIN_EMAIL", "admin.demo@example.com")
ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "AdminPassword789!")

# ==================== 知识库配置（可自定义） ====================
KB_A_NAME = os.getenv("DEMO_KB_A_NAME", "AI Research Papers")
KB_A_DESCRIPTION = os.getenv("DEMO_KB_A_DESCRIPTION", "Collection of AI and Machine Learning research papers")

KB_B_NAME = os.getenv("DEMO_KB_B_NAME", "History Documents")
KB_B_DESCRIPTION = os.getenv("DEMO_KB_B_DESCRIPTION", "Historical documents and archives")


def validate_config():
    """验证配置是否完整"""
    required_vars = [
        "SERVER_HOST",
        "POSTGRES_HOST",
        "POSTGRES_DATABASE",
        "POSTGRES_USER",
        "LLM_MODEL",
        "EMBEDDING_MODEL",
    ]
    
    missing = []
    for var in required_vars:
        if not globals().get(var):
            missing.append(var)
    
    if missing:
        raise ValueError(f"缺少必需的配置变量：{missing}")
    
    print("✓ 配置验证通过")
    print(f"  • 服务器：{SERVER_HOST}")
    print(f"  • 数据库：{POSTGRES_DATABASE}@{POSTGRES_HOST}")
    print(f"  • LLM 模型：{LLM_MODEL}")
    print(f"  • Embedding 模型：{EMBEDDING_MODEL}")
    return True


if __name__ == "__main__":
    print("=== 演示配置检查 ===\n")
    try:
        validate_config()
        print("\n✓ 所有必需配置已设置")
    except ValueError as e:
        print(f"\n✗ 配置错误：{e}")
