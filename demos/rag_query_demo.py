"""
RAG 查询功能演示脚本

时长：15 分钟
覆盖内容:
- Naive 模式查询
- Local 模式查询
- Global 模式查询
- 三种模式对比分析

使用方法:
    python rag_query_demo.py
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

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
    KB_A_NAME,
    TEST_QUERIES,
    VERBOSE_MODE,
    HTTP_TIMEOUT,
    QUERY_TIMEOUT,
)


class QueryDemo:
    """查询演示类"""
    
    def __init__(self):
        self.logger = DemoLogger(verbose=VERBOSE_MODE)
        self.client = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        self.kb_id = None
        self.results = {}
    
    async def run(self):
        """运行查询演示"""
        try:
            # ========== 步骤 1: 登录 ==========
            await self.step1_login()
            
            # ========== 步骤 2: 选择知识库 ==========
            await self.step2_select_kb()
            
            # ========== 步骤 3: Naive 模式查询 ==========
            await self.step3_naive_query()
            
            # ========== 步骤 4: Local 模式查询 ==========
            await self.step4_local_query()
            
            # ========== 步骤 5: Global 模式查询 ==========
            await self.step5_global_query()
            
            # ========== 步骤 6: 对比分析 ==========
            await self.step6_comparison()
            
            # ========== 总结 ==========
            self.summary()
            
        except KeyboardInterrupt:
            self.logger.warning("演示被用户中断")
        except Exception as e:
            self.logger.error(f"演示失败：{str(e)}")
            if VERBOSE_MODE:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    async def step1_login(self):
        """步骤 1: 登录"""
        print_section("步骤 1: 用户登录", "=")
        
        self.logger.info(f"使用账号登录：{USER_A_EMAIL}")
        
        login_data = {
            "email": USER_A_EMAIL,
            "password": USER_A_PASSWORD
        }
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/auth/login",
                json=login_data
            )
            
            access_token = response.get("access_token")
            self.client.set_token(access_token)
            self.logger.success("✓ 登录成功")
            
        except Exception as e:
            self.logger.error(f"登录失败：{e}")
            raise
    
    async def step2_select_kb(self):
        """步骤 2: 选择知识库"""
        print_section("步骤 2: 选择知识库", "=")
        
        self.logger.info("获取用户的知识库列表...")
        
        kbs_response = await self.client.get(f"{API_PREFIX}/knowledge-bases")
        # APIClient 返回的是 list，不是 dict
        kbs = kbs_response if isinstance(kbs_response, list) else kbs_response.get("items", [])
        
        if not kbs:
            self.logger.error("没有找到可用的知识库")
            self.logger.info("请先运行：python demos/quick_demo.py 创建知识库")
            sys.exit(1)
        
        self.logger.success(f"找到 {len(kbs)} 个知识库")
        
        # 显示所有知识库
        print("\n可用知识库:")
        for i, kb in enumerate(kbs, 1):
            print(f"  {i}. {kb['name']} (ID: {kb['id']})")
        
        # 选择第一个知识库（或根据名称匹配）
        selected_kb = None
        for kb in kbs:
            if KB_A_NAME.lower() in kb['name'].lower():
                selected_kb = kb
                break
        
        if not selected_kb:
            selected_kb = kbs[0]  # 默认选择第一个
        
        self.kb_id = selected_kb['id']
        self.logger.info(f"选择的知识库：{selected_kb['name']}")
        self.logger.success(f"知识库 ID: {self.kb_id}")
    
    async def step3_naive_query(self):
        """步骤 3: Naive 模式查询"""
        print_section("步骤 3: Naive 模式查询", "=")
        
        query_text = "AI驱动的自适应业务识别系统的核心设计理念有哪些？"  # 具体问题，验证基本检索
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：naive (向量相似度搜索)")
        self.logger.info("适用场景：事实性问题、直接检索")
        
        query_data = {
            "query": query_text,
            "mode": "naive",
            "top_k": 5,
            "vlm_enhanced": False  # Disable VLM to avoid timeout
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            metadata = response.get("metadata", {})
            
            self.results["naive"] = {
                "answer": answer,
                "duration": duration,
                "metadata": metadata
            }
            
            if answer:
                self.logger.success(f"✓ 查询成功，耗时：{format_time(duration)}")
                
                # 显示答案摘要
                print_section("查询结果摘要", "-")
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"{Colors.CYAN}{answer_preview}{Colors.RESET}\n")
                
                # 显示元数据
                if metadata:
                    print_result("检索到的文档块数", metadata.get("chunks_count", 0))
                    print_result("使用的 LLM", metadata.get("llm_model", "unknown"))
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                self.logger.info("可能原因：知识库中没有相关内容")
                
        except Exception as e:
            self.logger.error(f"✗ 查询失败：{e}")
            self.results["naive"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step4_local_query(self):
        """步骤 4: Hybrid 模式查询"""
        print_section("步骤 4: Hybrid 模式查询", "=")
        
        query_text = "系统架构中的 PAOLUR 流程具体指什么？每个步骤的作用是什么？"  # 具体问题，验证对比分析
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid (混合检索)")
        self.logger.info("适用场景：综合检索、平衡准确性和召回率")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "vlm_enhanced": False  # Disable VLM to avoid timeout
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            metadata = response.get("metadata", {})
            
            self.results["hybrid"] = {
                "answer": answer,
                "duration": duration,
                "metadata": metadata
            }
            
            if answer:
                self.logger.success(f"✓ 查询成功，耗时：{format_time(duration)}")
                
                # 显示答案摘要
                print_section("查询结果摘要", "-")
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"{Colors.CYAN}{answer_preview}{Colors.RESET}\n")
                
                # 显示元数据
                if metadata:
                    print_result("检索到的文档块数", metadata.get("chunks_count", 0))
                    print_result("使用的检索方式", metadata.get("retrieval_mode", "hybrid"))
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 查询失败：{e}")
            self.results["hybrid"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step5_global_query(self):
        """步骤 5: Mix 模式查询"""
        print_section("步骤 5: Mix 模式查询", "=")
        
        query_text = "系统的六个主要模块（Plan/Act/Observe/Learn/Update/Report）各自有什么功能和风险？"  # 具体问题，验证深度理解
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：mix (多策略融合)")
        self.logger.info("适用场景：复杂推理、全局理解")
        
        query_data = {
            "query": query_text,
            "mode": "mix",
            "top_k": 5,
            "vlm_enhanced": False  # Disable VLM to avoid timeout
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            metadata = response.get("metadata", {})
            
            self.results["mix"] = {
                "answer": answer,
                "duration": duration,
                "metadata": metadata
            }
            
            if answer:
                self.logger.success(f"✓ 查询成功，耗时：{format_time(duration)}")
                
                # 显示答案摘要
                print_section("查询结果摘要", "-")
                answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
                print(f"{Colors.CYAN}{answer_preview}{Colors.RESET}\n")
                
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 查询失败：{e}")
            self.results["mix"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step6_comparison(self):
        """步骤 6: 对比分析"""
        print_section("步骤 6: 三种模式对比", "=")
        
        self.logger.info("对比分析三种查询模式的性能和质量...")
        
        print("\n性能对比表:")
        print("-" * 70)
        print(f"{'模式':<15} {'耗时':<15} {'答案长度':<15} {'状态':<15}")
        print("-" * 70)
        
        for mode in ["naive", "hybrid", "mix"]:
            result = self.results.get(mode, {})
            
            if "error" in result:
                status = "❌ 失败"
                duration_str = format_time(result.get("duration", 0))
                answer_len = 0
            else:
                status = "✅ 成功"
                duration_str = format_time(result.get("duration", 0))
                answer_len = len(result.get("answer", ""))
            
            print(f"{mode.upper():<15} {duration_str:<15} {answer_len:<15} {status:<15}")
        
        print("-" * 70)
        
        # 分析建议
        print("\n模式特点分析:")
        print(f"\n1. Naive 模式:")
        print(f"   • 速度：通常最快")
        print(f"   • 质量：适合事实性问题")
        print(f"   • 场景：文档检索、关键词匹配")
        
        print(f"\n2. Hybrid 模式:")
        print(f"   • 速度：中等")
        print(f"   • 质量：综合效果好")
        print(f"   • 场景：大多数查询场景")
        
        print(f"\n3. Mix 模式:")
        print(f"   • 速度：根据组合策略而定")
        print(f"   • 质量：多角度检索")
        print(f"   • 场景：需要全面理解的复杂问题")
    
    def summary(self):
        """总结"""
        print_section("演示完成！", "=")
        
        self.logger.success("RAG 查询功能演示所有步骤已完成")
        
        print("\n演示总结:")
        print(f"  ✓ 测试的查询模式：3 种 (naive, hybrid, mix)")
        print(f"  ✓ 使用的知识库：{self.kb_id}")
        
        # 统计成功率
        success_count = sum(1 for r in self.results.values() if "error" not in r)
        total_count = len(self.results)
        
        print(f"  ✓ 查询成功率：{success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        print("\n关键发现:")
        print("  • Naive 模式适合快速检索")
        print("  • Hybrid 模式擅长平衡检索效果")
        print("  • Mix 模式强于多维度理解")
        print("  • 选择合适的模式取决于问题类型")
        
        print("\n下一步:")
        print("  1. 尝试不同的查询问题")
        print("  2. 调整 top_k 参数观察效果")
        print("  3. 查看完整演示：python demos/full_demo.py")
        print("  4. 清理数据：python demos/cleanup_demo.py")
        print()


async def main():
    """主函数"""
    demo = QueryDemo()
    await demo.run()


if __name__ == "__main__":
    print_section("RAG-Anything Server 查询功能演示", "=")
    print(f"{Colors.YELLOW}预计时长：15 分钟{Colors.RESET}")
    print(f"{Colors.YELLOW}复杂度：★★☆☆☆{Colors.RESET}\n")
    
    asyncio.run(main())
