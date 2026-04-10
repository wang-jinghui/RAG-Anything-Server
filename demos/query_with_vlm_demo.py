"""
VLM 增强查询功能演示脚本

时长：10-15 分钟
覆盖内容:
- VLM 增强查询 vs 普通查询对比
- 系统架构图理解测试
- PAOLUR 流程理解测试
- 性能对比分析

前置条件:
- 已上传包含图片的文档（如 AI驱动的自适应业务识别.pdf）
- 配置了 VLM 服务 (qwen3-vl:8b)
- 文档处理已完成

使用方法:
    python query_with_vlm_demo.py
"""

import asyncio
import sys
import time
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
    KB_A_NAME,
    VERBOSE_MODE,
    HTTP_TIMEOUT,
)


class VLMQueryDemo:
    """VLM 增强查询演示类"""
    
    def __init__(self):
        self.logger = DemoLogger(verbose=VERBOSE_MODE)
        self.client = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        self.kb_id = None
        self.results = {}
    
    async def run(self):
        """运行 VLM 增强查询演示"""
        try:
            # ========== 步骤 1: 登录 ==========
            await self.step1_login()
            
            # ========== 步骤 2: 选择知识库 ==========
            await self.step2_select_kb()
            
            # ========== 步骤 3: 检查知识库状态 ==========
            await self.step3_check_kb_status()
            
            # ========== 步骤 4: 普通查询（无 VLM）==========
            await self.step4_normal_query()
            
            # ========== 步骤 5: VLM 增强查询 - 架构图 ==========
            await self.step5_vlm_architecture_query()
            
            # ========== 步骤 6: VLM 增强查询 - PAOLUR 流程 ==========
            await self.step6_vlm_process_query()
            
            # ========== 步骤 7: 对比分析 ==========
            await self.step7_comparison()
            
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
            
            self.token = response.get("access_token")
            self.client.set_token(self.token)
            
            self.logger.success("✓ 登录成功")
            
        except Exception as e:
            self.logger.error(f"✗ 登录失败：{e}")
            raise
    
    async def step2_select_kb(self):
        """步骤 2: 选择知识库"""
        print_section("步骤 2: 选择知识库", "=")
        
        self.logger.info("获取用户的知识库列表...")
        
        try:
            response = await self.client.get(f"{API_PREFIX}/knowledge-bases")
            # API returns a list directly, not a dict with 'items' key
            kbs = response if isinstance(response, list) else response.get("items", [])
            
            if not kbs:
                self.logger.error("✗ 未找到可用的知识库")
                self.logger.info("请先运行 quick_demo.py 上传文档")
                sys.exit(1)
            
            self.logger.success(f"找到 {len(kbs)} 个知识库")
            
            # 选择第一个知识库
            kb = kbs[0]
            self.kb_id = kb.get("id")
            kb_name = kb.get("name", "Unknown")
            
            self.logger.info(f"选择的知识库：{kb_name}")
            self.logger.success(f"知识库 ID: {self.kb_id}")
            
        except Exception as e:
            self.logger.error(f"✗ 获取知识库列表失败：{e}")
            raise
    
    async def step3_check_kb_status(self):
        """步骤 3: 检查知识库状态"""
        print_section("步骤 3: 检查知识库状态", "=")
        
        self.logger.info("检查知识库中的文档和多媒体内容...")
        
        try:
            response = await self.client.get(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/documents"
            )
            
            documents = response.get("items", [])
            self.logger.success(f"找到 {len(documents)} 个文档")
            
            # 统计文档状态
            completed_docs = [d for d in documents if d.get("status") == "completed"]
            self.logger.info(f"已处理完成的文档：{len(completed_docs)}/{len(documents)}")
            
            if not completed_docs:
                self.logger.warning("⚠️  没有已处理完成的文档")
                self.logger.info("请等待文档处理完成后再进行测试")
            
            # 显示文档列表
            print("\n文档列表:")
            for i, doc in enumerate(documents, 1):
                status = doc.get("status", "unknown")
                name = doc.get("filename", "unknown")
                print(f"  {i}. {name} (状态: {status})")
            
        except Exception as e:
            self.logger.error(f"✗ 检查知识库状态失败：{e}")
            raise
    
    async def step4_normal_query(self):
        """步骤 4: 普通查询（无 VLM）"""
        print_section("步骤 4: 普通查询（无 VLM 增强）", "=")
        
        query_text = "AI驱动的自适应业务识别系统的六个主要模块（PAOLUR）分别是什么？每个模块的核心功能是什么？"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid (禁用 VLM)")
        self.logger.info("说明：此查询仅使用文本检索，不启用 VLM 增强")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "vlm_enhanced": False  # 明确禁用 VLM
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            images = response.get("images", None)
            
            self.results["normal"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "has_images": images is not None and len(images) > 0 if images else False
            }
            
            if answer:
                self.logger.success(f"✓ 查询成功，耗时：{format_time(duration)}")
                
                print_section("查询结果摘要", "-")
                # 只显示前 500 字符
                preview = answer[:500] + "..." if len(answer) > 500 else answer
                print(f"{Colors.CYAN}{preview}{Colors.RESET}\n")
                
                # 检查是否返回图片
                if images:
                    self.logger.warning(f"⚠️  意外返回了 {len(images)} 张图片信息")
                    self.logger.info("普通查询不应该返回图片元数据")
                else:
                    self.logger.info("✓ 正确：未返回图片元数据（符合预期）")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 查询失败：{e}")
            self.results["normal"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step5_vlm_architecture_query(self):
        """步骤 5: VLM 增强查询 - 系统架构图"""
        print_section("步骤 5: VLM 增强查询 - 系统架构图理解", "=")
        
        query_text = "文档中的系统架构图展示了什么？请详细描述图中的六个模块（Plan/Act/Observe/Learn/Update/Report）以及它们之间的关系和数据流向。"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + VLM 增强")
        self.logger.info("说明：此查询会启用 VLM 来理解系统架构图")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "vlm_enhanced": True  # 启用 VLM 增强
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            images = response.get("images", None)
            
            self.results["vlm_architecture"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "has_images": images is not None and len(images) > 0 if images else False
            }
            
            if answer:
                self.logger.success(f"✓ VLM 增强查询成功，耗时：{format_time(duration)}")
                
                print_section("VLM 查询结果摘要", "-")
                # 只显示前 500 字符
                preview = answer[:500] + "..." if len(answer) > 500 else answer
                print(f"{Colors.CYAN}{preview}{Colors.RESET}\n")
                
                # 检查是否返回图片
                if images:
                    self.logger.warning(f"⚠️  返回了 {len(images)} 张图片信息")
                    self.logger.info("VLM 增强查询不应该返回图片元数据，只返回文本答案")
                else:
                    self.logger.info("✓ 正确：未返回图片元数据，只返回 VLM 理解的文本")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ VLM 增强查询失败：{e}")
            import traceback
            traceback.print_exc()
            self.results["vlm_architecture"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step6_vlm_process_query(self):
        """步骤 6: VLM 增强查询 - PAOLUR 流程"""
        print_section("步骤 6: VLM 增强查询 - PAOLUR 闭环流程", "=")
        
        query_text = "如果文档中有展示 PAOLUR 闭环流程的图表，请解释这个感知-推理-学习-报告循环是如何工作的？每个阶段如何与下一个阶段衔接？"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + VLM 增强")
        self.logger.info("说明：此查询专注于理解系统工作流程图")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "vlm_enhanced": True  # 启用 VLM 增强
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            images = response.get("images", None)
            
            self.results["vlm_process"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "has_images": images is not None and len(images) > 0 if images else False
            }
            
            if answer:
                self.logger.success(f"✓ 流程图理解查询成功，耗时：{format_time(duration)}")
                
                print_section("流程图理解结果摘要", "-")
                # 只显示前 500 字符
                preview = answer[:500] + "..." if len(answer) > 500 else answer
                print(f"{Colors.CYAN}{preview}{Colors.RESET}\n")
                
                # 检查是否返回图片
                if images:
                    self.logger.warning(f"⚠️  返回了 {len(images)} 张图片信息")
                else:
                    self.logger.info("✓ 正确：未返回图片元数据")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 流程图理解查询失败：{e}")
            self.results["vlm_process"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step7_comparison(self):
        """步骤 7: 对比分析"""
        print_section("步骤 7: 查询模式对比分析", "=")
        
        self.logger.info("对比普通查询和 VLM 增强查询的效果...")
        
        # 准备对比数据
        normal_result = self.results.get("normal", {})
        vlm_arch_result = self.results.get("vlm_architecture", {})
        vlm_process_result = self.results.get("vlm_process", {})
        
        # 性能对比表
        print("\n性能对比表:")
        print("-" * 70)
        print(f"{'查询类型':<20} {'耗时':<15} {'答案长度':<15} {'状态'}")
        print("-" * 70)
        
        # 普通查询
        normal_duration = normal_result.get("duration", 0)
        normal_length = len(normal_result.get("answer", ""))
        normal_status = "✅ 成功" if "answer" in normal_result else "❌ 失败"
        print(f"{'普通查询':<20} {format_time(normal_duration):<15} {normal_length:<15} {normal_status}")
        
        # VLM 架构图查询
        vlm_arch_duration = vlm_arch_result.get("duration", 0)
        vlm_arch_length = len(vlm_arch_result.get("answer", ""))
        vlm_arch_status = "✅ 成功" if "answer" in vlm_arch_result else "❌ 失败"
        print(f"{'VLM-架构图':<20} {format_time(vlm_arch_duration):<15} {vlm_arch_length:<15} {vlm_arch_status}")
        
        # VLM 流程图查询
        vlm_process_duration = vlm_process_result.get("duration", 0)
        vlm_process_length = len(vlm_process_result.get("answer", ""))
        vlm_process_status = "✅ 成功" if "answer" in vlm_process_result else "❌ 失败"
        print(f"{'VLM-流程图':<20} {format_time(vlm_process_duration):<15} {vlm_process_length:<15} {vlm_process_status}")
        
        print("-" * 70)
        
        # 效果分析
        print("\n效果分析:")
        print("1. 响应时间对比:")
        if normal_duration > 0 and vlm_arch_duration > 0:
            speed_diff = ((vlm_arch_duration - normal_duration) / normal_duration) * 100
            if speed_diff > 0:
                print(f"   • VLM 增强查询比普通查询慢 {speed_diff:.1f}%")
            else:
                print(f"   • VLM 增强查询比普通查询快 {abs(speed_diff):.1f}%")
        
        print("\n2. 答案质量对比:")
        print("   • 普通查询: 基于文本检索，适合事实性问题")
        print("   • VLM 增强查询: 结合图片理解，适合图表、架构图等视觉内容")
        
        print("\n3. 适用场景:")
        print("   • 普通查询: 快速检索文档中的文本信息")
        print("   • VLM 增强查询: 需要理解图片、图表、架构图等视觉内容")
    
    def summary(self):
        """总结"""
        print_section("演示完成！", "=")
        
        self.logger.success("VLM 增强查询功能演示所有步骤已完成")
        
        print("\n演示总结:")
        print(f"  ✓ 测试的查询类型：3 种 (普通、VLM-架构图、VLM-流程图)")
        print(f"  ✓ 使用的知识库：{self.kb_id}")
        
        # 计算成功率
        total_tests = 3
        successful_tests = sum(1 for key in ["normal", "vlm_architecture", "vlm_process"] 
                              if "answer" in self.results.get(key, {}))
        print(f"  ✓ 查询成功率：{successful_tests}/{total_tests} ({successful_tests/total_tests*100:.0f}%)")
        
        print("\n关键发现:")
        print("  • 普通查询速度快，适合纯文本检索")
        print("  • VLM 增强查询能理解图片和图表内容")
        print("  • VLM 增强查询只返回文本答案，不返回图片元数据")
        print("  • 选择合适的查询方式取决于问题类型和内容形式")
        
        print("\n下一步:")
        print("  1. 尝试不同的查询问题")
        print("  2. 调整 top_k 参数观察效果")
        print("  3. 测试多模态查询端点：POST /api/v1/knowledge-bases/{kb_id}/multimodal-query")
        print("  4. 清理数据：python demos/cleanup_demo.py")


async def main():
    """主函数"""
    print("=" * 70)
    print("  RAG-Anything Server VLM 增强查询演示")
    print("=" * 70)
    print("预计时长：10-15 分钟")
    print("复杂度：★★☆☆☆")
    print("前置条件：")
    print("  • 已上传包含图片的文档")
    print("  • 配置了 VLM 服务 (qwen3-vl:8b)")
    print("  • 文档处理已完成")
    print("=" * 70)
    print()
    
    demo = VLMQueryDemo()
    await demo.run()


if __name__ == "__main__":
    asyncio.run(main())
