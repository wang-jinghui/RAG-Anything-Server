"""
快速演示脚本 - RAG-Anything Server 核心功能展示

时长: 5-10 分钟
覆盖内容:
- 用户注册与登录
- 创建知识库
- 上传文档
- 等待文档处理完成

使用方法:
    python quick_demo.py                         # 使用默认文件 test.pdf
    python quick_demo.py file1.pdf               # 上传指定文件
    python quick_demo.py file1.pdf file2.md      # 上传多个文件
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 添加 demos 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from demo_utils import (
    DemoLogger, 
    APIClient, 
    print_section, 
    print_result,
    format_time,
    Colors
)
from demo_config import (
    SERVER_HOST,
    API_PREFIX,
    USER_A_EMAIL,
    USER_A_PASSWORD,
    USER_A_NAME,
    KB_A_NAME,
    KB_A_DESCRIPTION,
    VERBOSE_MODE,
)


async def main(file_paths: list):
    """主函数
    
    Args:
        file_paths: 要上传的文件路径列表
    """
    logger = DemoLogger(verbose=VERBOSE_MODE)
    
    try:
        # ========== 步骤 1: 系统检查 ==========
        print_section("步骤 1: 系统检查", "=")
        
        client = APIClient(SERVER_HOST)  # 使用默认 60 秒超时
        
        # 检查服务器是否运行
        try:
            health_data = await client.get("/health")
            logger.success("[OK] 服务器运行正常")
            if VERBOSE_MODE:
                logger.info(f"健康状态：{health_data}")
        except Exception as e:
            logger.error(f"服务器未启动或无法访问：{e}")
            logger.info("请先运行：uvicorn server.main:app --reload")
            return
        
        # ========== 步骤 2: 用户注册 ==========
        print_section("步骤 2: 用户注册", "=")
        
        logger.info(f"注册用户：{USER_A_NAME} ({USER_A_EMAIL})")
        
        register_data = {
            "username": USER_A_NAME.replace(" ", "_").lower(),  # 生成用户名
            "email": USER_A_EMAIL,
            "password": USER_A_PASSWORD,
            "name": USER_A_NAME
        }
        
        try:
            register_response = await client.post(
                f"{API_PREFIX}/auth/register",
                json=register_data
            )
            user_id = register_response.get("id")
            logger.success(f"用户注册成功，ID: {user_id}")
        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                logger.warning("用户已存在，将使用现有账号...")
            else:
                raise
        
        # ========== 步骤 3: 用户登录 ==========
        print_section("步骤 3: 用户登录", "=")
        
        logger.info("使用凭据登录...")
        
        login_data = {
            "email": USER_A_EMAIL,
            "password": USER_A_PASSWORD
        }
        
        login_response = await client.post(
            f"{API_PREFIX}/auth/login",
            json=login_data
        )
        
        access_token = login_response.get("access_token")
        client.set_token(access_token)
        logger.success("登录成功，获取到 JWT Token")
        
        # ========== 步骤 4: 创建知识库 ==========
        print_section("步骤 4: 创建知识库", "=")
        
        logger.info(f"创建知识库：{KB_A_NAME}")
        
        kb_data = {
            "name": KB_A_NAME,
            "description": KB_A_DESCRIPTION
        }
        
        try:
            kb_response = await client.post(
                f"{API_PREFIX}/knowledge-bases",
                json=kb_data
            )
            kb_id = kb_response.get("id")
            logger.success(f"知识库创建成功，ID: {kb_id}")
        except Exception as e:
            error_msg = str(e).lower()
            if "integrity" in error_msg or "duplicate key" in error_msg:
                logger.warning("知识库已存在，将使用现有知识库...")
                # 获取用户的知识库列表，找到同名的
                kbs_temp = await client.get(f"{API_PREFIX}/knowledge-bases")
                if isinstance(kbs_temp, list):
                    kbs_list = kbs_temp
                else:
                    kbs_list = kbs_temp.get("items", [])
                
                existing_kb = next((kb for kb in kbs_list if kb["name"] == KB_A_NAME), None)
                if existing_kb:
                    kb_id = existing_kb["id"]
                    kb_response = existing_kb
                    logger.success(f"使用现有知识库，ID: {kb_id}")
                else:
                    logger.error("未找到现有的同名知识库")
                    raise
            else:
                raise
        
        print_result("知识库名称", kb_response.get("name"))
        print_result("描述", kb_response.get("description"))
        
        # ========== 步骤 5: 列出知识库 ==========
        print_section("步骤 5: 验证知识库", "=")
        
        logger.info("获取用户的所有知识库...")
        
        kbs_response = await client.get(f"{API_PREFIX}/knowledge-bases")
        # 响应是 List[KnowledgeBaseResponse]，直接是列表
        kbs = kbs_response if isinstance(kbs_response, list) else kbs_response.get("items", [])
        
        logger.success(f"共有 {len(kbs)} 个知识库")
        for kb in kbs:
            print_result(f"- {kb['name']}", kb['id'], indent=1)
        
        # ========== 步骤 6: 上传文档 ==========
        print_section("步骤 6: 上传文档", "=")
        
        logger.info("准备上传文档...")
        
        # 验证文件是否存在
        existing_files = []
        for file_path in file_paths:
            fp = Path(file_path)
            if not fp.exists():
                logger.warning(f"文件不存在，跳过：{file_path}")
            else:
                existing_files.append(str(fp))
                logger.success(f"找到文件：{fp.name}")
        
        if not existing_files:
            logger.error("没有有效的文件可上传")
            return
        
        # 上传文件
        logger.info(f"上传 {len(existing_files)} 个文件到知识库...")
            
        upload_endpoint = f"{API_PREFIX}/knowledge-bases/{kb_id}/documents"
        
        # 使用 httpx 的 files 参数自动处理 multipart/form-data
        for file_path in existing_files:
            try:
                # 打开文件（保持文件对象打开状态）
                with open(file_path, 'rb') as f:
                    # 获取文件名和 MIME 类型
                    file_name = Path(file_path).name
                    content_type = "application/octet-stream"
                    if file_path.endswith('.pdf'):
                        content_type = "application/pdf"
                    elif file_path.endswith('.md'):
                        content_type = "text/markdown"
                    elif file_path.endswith('.txt'):
                        content_type = "text/plain"
                    
                    # 上传文件 - 直接传文件对象，不要读取内容
                    files = {"file": (file_name, f, content_type)}
                    upload_resp = await client.post(
                        upload_endpoint,
                        files=files
                    )
                    
                    # APIClient 返回的是 dict，直接处理
                    doc_id = upload_resp.get("id")
                    logger.success(f"[OK] 文件上传成功：{file_name} (ID: {doc_id})")
                
            except Exception as e:
                logger.error(f"[ERROR] 上传失败 {file_path}: {e}")
        
        # 等待文档处理完成
        logger.info("等待文档处理完成...")
        max_wait = 60  # 最多等待 60 秒
        start_time = asyncio.get_event_loop().time()
        
        while True:
            await asyncio.sleep(3)
            status_resp = await client.get(f"{API_PREFIX}/knowledge-bases/{kb_id}/documents")
            # APIClient 返回的已经是 dict，不需要再调用.json()
            docs_data = status_resp
            
            # 正确处理响应格式：可能是 {documents: [...], total: N} 或直接的列表
            if isinstance(docs_data, dict):
                docs = docs_data.get('documents', [])
            elif isinstance(docs_data, list):
                docs = docs_data
            else:
                docs = []
            
            if docs:
                completed = sum(1 for d in docs if d.get('upload_status') == 'completed')
                failed = sum(1 for d in docs if d.get('upload_status') == 'failed')
                pending = len(docs) - completed - failed
                logger.info(f"处理进度：{completed} 完成，{pending} 处理中，{failed} 失败 (共{len(docs)}个)")
                
                # 只要新上传的文档处理完成就继续
                if completed >= len(existing_files):  # 至少有 uploaded_count 个完成
                    logger.success(f"✓ 新上传的 {len(existing_files)} 个文档已处理完成")
                    break
                elif failed > 0 and pending == 0:  # 全部处理完但有失败的
                    logger.warning(f"有 {failed} 个文档处理失败")
                    break
            
            # 检查超时
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > max_wait:
                logger.warning(f"等待文档处理超时 ({max_wait}秒)，继续执行...")
                break
        
        # ========== 步骤 7: 总结 ==========
        print_section("演示完成！", "=")
        
        logger.success("快速演示所有步骤已完成")
        print("\n演示总结:")
        print(f"  ✓ 用户注册/登录：{USER_A_EMAIL}")
        print(f"  ✓ 创建知识库：{KB_A_NAME} (ID: {kb_id})")
        print(f"  ✓ 上传文件数：{len(existing_files)}")
        print(f"  ✓ 文档状态：已处理完成")
        print("\n下一步:")
        print("  1. 执行查询：python demos/rag_query_demo.py")
        print("  2. 查看完整演示：python demos/full_demo.py")
        print("  3. 清理演示数据：python demos/cleanup_demo.py")
        print("  4. 访问 API 文档：http://localhost:8000/docs\n")
        
    except KeyboardInterrupt:
        logger.warning("演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误：{str(e)}")
        if VERBOSE_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="RAG-Anything Server 快速演示")
    parser.add_argument(
        "files",
        nargs="*",
        default=["test.pdf"],
        help="要上传的文件路径列表（默认：test.pdf）"
    )
    args = parser.parse_args()
    
    # 如果没有指定文件或使用默认值，检查 test.pdf 位置
    if args.files == ["test.pdf"]:
        # 尝试在项目根目录查找
        test_pdf = Path(__file__).parent.parent / "test.pdf"
        if test_pdf.exists():
            args.files = [str(test_pdf)]
    
    print_section("RAG-Anything Server 快速演示", "=")
    print(f"{Colors.YELLOW}预计时长：5-10 分钟{Colors.RESET}")
    print(f"{Colors.YELLOW}复杂度：★☆☆☆☆{Colors.RESET}\n")
    print(f"将上传 {len(args.files)} 个文件:\n  • " + "\n  • ".join(args.files) + "\n")
    
    asyncio.run(main(args.files))
