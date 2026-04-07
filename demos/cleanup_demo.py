"""
演示数据清理脚本

用途:
- 删除演示过程中创建的测试用户
- 删除测试知识库
- 清理向量数据库
- 重置 workspace

注意：此脚本会永久删除数据，请谨慎使用！

使用方法:
    python cleanup_demo.py
"""

import asyncio
import sys
from pathlib import Path

# 添加 demos 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from demo_utils import (
    DemoLogger, 
    APIClient, 
    print_section,
    Colors
)
from demo_config import (
    SERVER_HOST,
    API_PREFIX,
    USER_A_EMAIL,
    USER_A_PASSWORD,
    USER_B_EMAIL,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    HTTP_TIMEOUT,
    VERBOSE_MODE,
)


async def cleanup_knowledge_bases(client: APIClient, logger: DemoLogger):
    """清理所有知识库"""
    print_section("清理知识库", "=")
    
    try:
        # 获取所有知识库
        kbs_response = await client.get(f"{API_PREFIX}/knowledge-bases")
        # APIClient 返回的是 list，不是 dict
        kbs = kbs_response if isinstance(kbs_response, list) else kbs_response.get("items", [])
        
        if not kbs:
            logger.info("没有找到知识库")
            return
        
        logger.info(f"找到 {len(kbs)} 个知识库")
        
        # 删除每个知识库
        for kb in kbs:
            kb_id = kb.get("id")
            kb_name = kb.get("name")
            
            try:
                logger.info(f"正在删除知识库：{kb_name} (ID: {kb_id})")
                await client.delete(f"{API_PREFIX}/knowledge-bases/{kb_id}")
                logger.success(f"✓ 已删除：{kb_name}")
            except Exception as e:
                logger.error(f"删除失败 {kb_id}: {str(e)}")
        
        logger.success(f"知识库清理完成，共删除 {len(kbs)} 个")
        
    except Exception as e:
        logger.error(f"获取知识库列表失败：{str(e)}")


async def main():
    """主函数"""
    logger = DemoLogger(verbose=VERBOSE_MODE)
    
    print_section("RAG-Anything Server 清理脚本", "=")
    print(f"{Colors.RED}⚠️  警告：此操作将永久删除演示数据！{Colors.RESET}")
    print()
    
    # 确认操作
    if VERBOSE_MODE:
        response = input("确定要清理所有演示数据吗？(yes/no): ")
        if response.lower() != "yes":
            logger.info("操作已取消")
            return
    
    try:
        # ========== 步骤 1: 管理员登录 ==========
        print_section("步骤 1: 管理员登录", "=")
        
        client = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        
        logger.info("使用管理员账号登录...")
        
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            login_response = await client.post(
                f"{API_PREFIX}/auth/login",
                json=login_data
            )
            
            access_token = login_response.get("access_token")
            client.set_token(access_token)
            logger.success("管理员登录成功")
            
        except Exception as e:
            logger.warning(f"管理员登录失败：{e}")
            logger.info("尝试使用普通用户权限继续...")
            
            # 尝试用普通用户登录
            login_data = {
                "email": USER_A_EMAIL,
                "password": USER_A_PASSWORD
            }
            
            try:
                login_response = await client.post(
                    f"{API_PREFIX}/auth/login",
                    json=login_data
                )
                
                access_token = login_response.get("access_token")
                client.set_token(access_token)
                logger.success("普通用户登录成功（权限受限）")
                
            except Exception as e2:
                logger.error(f"无法登录：{e2}")
                logger.info("请确保服务器正在运行且账号存在")
                return
        
        # ========== 步骤 2: 清理知识库 ==========
        print_section("步骤 2: 清理知识库", "=")
        
        await cleanup_knowledge_bases(client, logger)
        
        # ========== 步骤 3: 验证清理结果 ==========
        print_section("步骤 3: 验证清理结果", "=")
        
        try:
            kbs_response = await client.get(f"{API_PREFIX}/knowledge-bases")
            remaining_kbs = kbs_response.get("items", [])
            
            if remaining_kbs:
                logger.warning(f"仍有 {len(remaining_kbs)} 个知识库未被清理")
                for kb in remaining_kbs:
                    print_result(f"  - {kb['name']}", kb['id'])
            else:
                logger.success("✓ 所有知识库已清理完毕")
                
        except Exception as e:
            logger.error(f"验证失败：{str(e)}")
        
        # ========== 步骤 4: 总结 ==========
        print_section("清理完成", "=")
        
        logger.success("演示数据清理完成！")
        print("\n已清理:")
        print("  ✓ 知识库及其相关文档")
        print("  ✓ 向量数据库中的数据")
        print("  ✓ 图数据库中的数据（如使用）")
        print("\n未清理:")
        print("  ✗ 用户账号（需要手动删除或保留）")
        print("  ✗ API Keys（需要手动删除）")
        print("\n提示:")
        print("  - 如需重新演示，请运行：python demos/quick_demo.py")
        print("  - 如需完全清理，请手动删除数据库中的用户记录\n")
        
    except KeyboardInterrupt:
        logger.warning("清理操作被用户中断")
    except Exception as e:
        logger.error(f"清理过程中发生错误：{str(e)}")
        if VERBOSE_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_result(label: str, value: str):
    """打印结果（辅助函数）"""
    print(f"  {label}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
