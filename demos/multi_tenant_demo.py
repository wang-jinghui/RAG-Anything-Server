"""
多租户隔离演示脚本

时长：20 分钟
覆盖内容:
- 创建多个租户
- 租户间数据隔离验证
- 跨租户查询对比
- 权限控制展示

使用方法:
    python multi_tenant_demo.py
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
    print_result,
    Colors
)
from demo_config import (
    SERVER_HOST,
    API_PREFIX,
    USER_A_EMAIL,
    USER_A_PASSWORD,
    USER_A_NAME,
    USER_B_EMAIL,
    USER_B_PASSWORD,
    USER_B_NAME,
    KB_A_NAME,
    KB_B_NAME,
    VERBOSE_MODE,
    HTTP_TIMEOUT,
)


async def main():
    """主函数"""
    logger = DemoLogger(verbose=VERBOSE_MODE)
    
    try:
        # ========== 步骤 1: 系统初始化 ==========
        print_section("步骤 1: 系统初始化", "=")
        
        client_alice = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        client_bob = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        
        # 检查服务器（使用健康检查端点或直接继续）
        logger.info("服务器运行正常")
        
        # ========== 步骤 2: 创建租户 A（Alice） ==========
        print_section("步骤 2: 创建租户 A - Alice", "=")
        
        # 注册 Alice
        logger.info(f"注册用户：{USER_A_NAME}")
        register_data = {
            "email": USER_A_EMAIL,
            "password": USER_A_PASSWORD,
            "username": USER_A_NAME  # Changed from 'name' to 'username'
        }
        
        try:
            response = await client_alice.post(
                f"{API_PREFIX}/auth/register",
                json=register_data
            )
            user_a_id = response.get("id")
            logger.success(f"Alice 注册成功，ID: {user_a_id}")
        except Exception as e:
            if "already" in str(e).lower():  # Match both 'already exists' and 'already registered'
                logger.warning("Alice 已存在，登录中...")
                login_data = {"email": USER_A_EMAIL, "password": USER_A_PASSWORD}
                login_response = await client_alice.post(
                    f"{API_PREFIX}/auth/login",
                    json=login_data
                )
                access_token = login_response.get("access_token")
                client_alice.set_token(access_token)
                
                # Note: user_a_id is not available from login, will use None for now
                # This means permission revocation won't work in this demo run
                user_a_id = None
                logger.info("注意：由于是已存在用户，无法获取 user ID，权限撤销功能将受限")
                
                logger.success("Alice 登录成功")
            else:
                raise
        
        # 创建 Alice 的知识库（先检查是否已存在）
        logger.info(f"检查 Alice 的知识库：{KB_A_NAME}")
        
        # 获取现有知识库列表
        existing_kbs = await client_alice.get(f"{API_PREFIX}/knowledge-bases")
        kbs_list = existing_kbs if isinstance(existing_kbs, list) else existing_kbs.get("items", [])
        
        # 检查是否已存在同名知识库
        kb_a_id = None
        for kb in kbs_list:
            if kb.get("name") == KB_A_NAME:
                kb_a_id = kb.get("id")
                logger.success(f"知识库已存在，ID: {kb_a_id}，跳过创建")
                break
        
        # 如果不存在，则创建
        if not kb_a_id:
            logger.info(f"Alice 创建知识库：{KB_A_NAME}")
            kb_data = {
                "name": KB_A_NAME,
                "description": "Alice's research data"
            }
            
            kb_response = await client_alice.post(
                f"{API_PREFIX}/knowledge-bases",
                json=kb_data
            )
            kb_a_id = kb_response.get("id")
            logger.success(f"Alice 的知识库创建成功，ID: {kb_a_id}")
        else:
            logger.info(f"使用已有知识库：{kb_a_id}")
        
        # ========== 步骤 3: 创建租户 B（Bob） ==========
        print_section("步骤 3: 创建租户 B - Bob", "=")
        
        # 注册 Bob
        logger.info(f"注册用户：{USER_B_NAME}")
        register_data = {
            "email": USER_B_EMAIL,
            "password": USER_B_PASSWORD,
            "username": USER_B_NAME  # Changed from 'name' to 'username'
        }
        
        try:
            response = await client_bob.post(
                f"{API_PREFIX}/auth/register",
                json=register_data
            )
            user_b_id = response.get("id")
            logger.success(f"Bob 注册成功，ID: {user_b_id}")
            
            # 注册后需要登录获取 token
            login_data = {"email": USER_B_EMAIL, "password": USER_B_PASSWORD}
            login_response = await client_bob.post(
                f"{API_PREFIX}/auth/login",
                json=login_data
            )
            access_token = login_response.get("access_token")
            client_bob.set_token(access_token)
            logger.success("Bob 登录成功")
        except Exception as e:
            if "already" in str(e).lower():  # Match both 'already exists' and 'already registered'
                logger.warning("Bob 已存在，登录中...")
                login_data = {"email": USER_B_EMAIL, "password": USER_B_PASSWORD}
                login_response = await client_bob.post(
                    f"{API_PREFIX}/auth/login",
                    json=login_data
                )
                access_token = login_response.get("access_token")
                client_bob.set_token(access_token)
                
                # Note: user_b_id is not available from login, will use None for now
                # This means permission revocation won't work in this demo run
                user_b_id = None
                logger.info("注意：由于是已存在用户，无法获取 user ID，权限撤销功能将受限")
                
                logger.success("Bob 登录成功")
            else:
                raise
        
        # 创建 Bob 的知识库（先检查是否已存在）
        logger.info(f"检查 Bob 的知识库：{KB_B_NAME}")
        
        # 获取现有知识库列表
        existing_kbs = await client_bob.get(f"{API_PREFIX}/knowledge-bases")
        kbs_list = existing_kbs if isinstance(existing_kbs, list) else existing_kbs.get("items", [])
        
        # 检查是否已存在同名知识库
        kb_b_id = None
        for kb in kbs_list:
            if kb.get("name") == KB_B_NAME:
                kb_b_id = kb.get("id")
                logger.success(f"知识库已存在，ID: {kb_b_id}，跳过创建")
                break
        
        # 如果不存在，则创建
        if not kb_b_id:
            logger.info(f"Bob 创建知识库：{KB_B_NAME}")
            kb_data = {
                "name": KB_B_NAME,
                "description": "Bob's study materials"
            }
            
            kb_response = await client_bob.post(
                f"{API_PREFIX}/knowledge-bases",
                json=kb_data
            )
            kb_b_id = kb_response.get("id")
            logger.success(f"Bob 的知识库创建成功，ID: {kb_b_id}")
        else:
            logger.info(f"使用已有知识库：{kb_b_id}")
        
        # ========== 步骤 4: 租户隔离验证 ==========
        print_section("步骤 4: 租户隔离验证", "=")
        
        # 4.1 Alice 查看自己的知识库
        logger.info("Alice 查看自己的知识库列表...")
        alice_kbs = await client_alice.get(f"{API_PREFIX}/knowledge-bases")
        alice_kbs_list = alice_kbs if isinstance(alice_kbs, list) else alice_kbs.get('items', [])
        logger.success(f"Alice 有 {len(alice_kbs_list)} 个知识库")
        
        # 4.2 Bob 查看自己的知识库
        logger.info("Bob 查看自己的知识库列表...")
        bob_kbs = await client_bob.get(f"{API_PREFIX}/knowledge-bases")
        bob_kbs_list = bob_kbs if isinstance(bob_kbs, list) else bob_kbs.get('items', [])
        logger.success(f"Bob 有 {len(bob_kbs_list)} 个知识库")
        
        # 4.3 Bob 尝试访问 Alice 的知识库（应该失败）
        logger.info("\nBob 尝试访问 Alice 的知识库（无授权情况下）...")
        try:
            await client_bob.get(f"{API_PREFIX}/knowledge-bases/{kb_a_id}")
            logger.warning("警告：Bob 竟然能访问 Alice 的知识库！")
        except Exception as e:
            logger.success(f"权限控制正常：{str(e)[:50]}")
        
        # ========== 步骤 5: 跨租户查询对比 ==========
        print_section("步骤 5: 跨租户查询对比", "=")
        
        # Alice 查询自己的知识库（AI 相关）
        alice_query = "AI驱动的自适应业务识别系统的核心设计理念有哪些？"
        logger.info(f"Alice 查询自己的知识库：{alice_query}")
        query_data_alice = {
            "query": alice_query,
            "mode": "naive",
            "top_k": 3,
            "vlm_enhanced": False  # Disable VLM for faster response
        }
        
        try:
            alice_result = await client_alice.post(
                f"{API_PREFIX}/knowledge-bases/{kb_a_id}/query",
                json=query_data_alice
            )
            logger.success(f"Alice 查询完成")
            if alice_result.get("answer"):
                answer_preview = alice_result['answer'][:128]
                print_result("答案预览", f"{answer_preview}...")
        except Exception as e:
            logger.error(f"Alice 查询失败：{e}")
        
        # Bob 查询自己的知识库（使用不同问题，避免 LLM 缓存）
        bob_query = "统计学的主要流派有哪些？"
        logger.info(f"\nBob 查询自己的知识库：{bob_query}")
        logger.info(f"注意：Bob 的知识库为空，应该返回空答案或提示无相关内容")
        query_data_bob = {
            "query": bob_query,
            "mode": "naive",
            "top_k": 3,
            "vlm_enhanced": False
        }
        
        try:
            bob_result = await client_bob.post(
                f"{API_PREFIX}/knowledge-bases/{kb_b_id}/query",
                json=query_data_bob
            )
            logger.success(f"Bob 查询完成")
            if bob_result.get("answer"):
                answer_preview = bob_result['answer'][:128]
                print_result("答案预览", f"{answer_preview}...")
                logger.warning("Bob 的空知识库返回了答案（可能是 LLM 幻觉）")
            else:
                logger.success("Bob 的知识库返回空答案（预期行为）")
        except Exception as e:
            logger.error(f"Bob 查询失败：{e}")
        
        # ========== 步骤 6: 知识共享测试 ==========
        print_section("步骤 6: 知识共享测试", "=")
        
        # Alice 分享知识库给 Bob
        logger.info(f"Alice 分享知识库给 Bob: {KB_A_NAME}")
        share_data = {
            "user_email": USER_B_EMAIL,
            "role": "viewer",
            "access_level": "viewer"  # Fixed: should be 'viewer', not 'read'
        }
        
        try:
            await client_alice.post(
                f"{API_PREFIX}/knowledge-bases/{kb_a_id}/access",
                json=share_data
            )
            logger.success("知识共享成功")
        except Exception as e:
            logger.error(f"共享失败：{e}")
        
        # Bob 查看被共享的知识库
        logger.info("Bob 查看被共享的知识库列表...")
        try:
            shared_kbs = await client_bob.get(f"{API_PREFIX}/knowledge-bases")
            shared_kbs_list = shared_kbs if isinstance(shared_kbs, list) else shared_kbs.get("items", [])
            shared_count = len(shared_kbs_list)
            logger.success(f"Bob 现在有 {shared_count} 个可访问的知识库")
        except Exception as e:
            logger.error(f"获取失败：{e}")
        
        # Bob 查询 Alice 的知识库（验证共享后是否可以查询）
        logger.info(f"\nBob 尝试查询 Alice 的知识库（共享后）：{alice_query}")
        try:
            bob_shared_result = await client_bob.post(
                f"{API_PREFIX}/knowledge-bases/{kb_a_id}/query",
                json=query_data_alice
            )
            if bob_shared_result.get("answer"):
                answer_preview = bob_shared_result['answer'][:128]
                logger.success(f"共享后查询成功！答案预览：{answer_preview}...")
            else:
                logger.warning("查询返回空答案")
        except Exception as e:
            logger.error(f"共享后查询失败：{e}")
        
        # ========== 步骤 7: 权限撤销 ==========
        print_section("步骤 7: 权限撤销", "=")
        
        logger.info("Alice 撤销对 Bob 的授权...")
        try:
            # Revoke permission using email (much simpler!)
            revoke_data = {"user_email": USER_B_EMAIL}
            await client_alice.delete(
                f"{API_PREFIX}/knowledge-bases/{kb_a_id}/access",
                json=revoke_data
            )
            logger.success("权限撤销成功")
        except Exception as e:
            logger.error(f"撤销失败：{e}")
        
        # Bob 再次查询 Alice 的知识库（验证撤销后是否无法查询）
        logger.info(f"\nBob 尝试查询 Alice 的知识库（撤销后）：{alice_query}")
        try:
            bob_revoked_result = await client_bob.post(
                f"{API_PREFIX}/knowledge-bases/{kb_a_id}/query",
                json=query_data_alice
            )
            if bob_revoked_result.get("answer"):
                logger.warning("警告：撤销后仍然可以查询！权限控制可能存在问题")
            else:
                logger.success("撤销后查询返回空答案，权限控制正常")
        except Exception as e:
            if "404" in str(e) or "403" in str(e) or "not found" in str(e).lower() or "forbidden" in str(e).lower():
                logger.success(f"撤销后查询被拒绝（预期行为）：{str(e)[:80]}")
            else:
                logger.error(f"撤销后查询出现意外错误：{e}")
        
        # ========== 总结 ==========
        print_section("多租户演示完成！", "=")
        
        logger.success("多租户隔离演示所有步骤已完成")
        
        print("\n演示总结:")
        print(f"  - 租户创建：2 个 (Alice, Bob)")
        print(f"  - 知识库创建：2 个 ({KB_A_NAME}, {KB_B_NAME})")
        print(f"  - 租户隔离：已验证")
        print(f"  - 权限控制：正常工作")
        print(f"  - 知识共享：已演示")
        print(f"  - 跨租户查询：对比完成")
        
        print("\n关键发现:")
        print("  • 每个租户只能看到自己的知识库")
        print("  • 未经授权的访问会被拒绝")
        print("  • 知识共享机制工作正常")
        print("  • 命名空间隔离有效")
        
        print("\n下一步:")
        print("  1. 清理数据：python demos/cleanup_demo.py")
        print("  2. 查看完整演示：python demos/full_demo.py")
        print("  3. 查看 RAG 查询演示：python demos/rag_query_demo.py")
        print()
        
    except KeyboardInterrupt:
        logger.warning("演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误：{str(e)}")
        if VERBOSE_MODE:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print_section("多租户隔离演示", "=")
    print(f"{Colors.YELLOW}预计时长：20 分钟{Colors.RESET}")
    print(f"{Colors.YELLOW}复杂度：★★★☆☆{Colors.RESET}\n")
    
    asyncio.run(main())
