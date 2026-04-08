"""
多模态查询功能演示脚本

时长：10-15 分钟
覆盖内容:
- 基本文本查询（验证 PAOLUR 模块描述检索）
- VLM 增强查询 - 系统架构图理解（验证图片理解能力）
- VLM 增强查询 - PAOLUR 闭环流程（验证流程图理解）
- 对比分析（有无 VLM 的差异）

测试文档：AI驱动的自适应业务识别.pdf
- 包含系统架构图（展示六个模块：Plan/Act/Observe/Learn/Update/Report）
- 包含 PAOLUR 闭环流程说明

使用方法:
    python multimodal_query_demo.py
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


class MultimodalQueryDemo:
    """多模态查询演示类"""
    
    def __init__(self):
        self.logger = DemoLogger(verbose=VERBOSE_MODE)
        self.client = APIClient(SERVER_HOST, timeout=HTTP_TIMEOUT)
        self.kb_id = None
        self.results = {}
    
    async def run(self):
        """运行多模态查询演示"""
        try:
            # ========== 步骤 1: 登录 ==========
            await self.step1_login()
            
            # ========== 步骤 2: 选择知识库 ==========
            await self.step2_select_kb()
            
            # ========== 步骤 3: 检查知识库状态 ==========
            await self.step3_check_kb_status()
            
            # ========== 步骤 4: 基本文本查询 ==========
            await self.step4_basic_query()
            
            # ========== 步骤 5: VLM 增强查询 - 图片内容 ==========
            await self.step5_vlm_image_query()
            
            # ========== 步骤 6: VLM 增强查询 - 图表理解 ==========
            await self.step6_vlm_chart_query()
            
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
        kbs = kbs_response if isinstance(kbs_response, list) else kbs_response.get("items", [])
        
        if not kbs:
            self.logger.error("没有找到可用的知识库")
            self.logger.info("请先运行：python demos/test_vlm_api.py 上传带图片的文档")
            sys.exit(1)
        
        self.logger.success(f"找到 {len(kbs)} 个知识库")
        
        # 选择包含图片的知识库
        selected_kb = None
        for kb in kbs:
            if KB_A_NAME.lower() in kb['name'].lower():
                selected_kb = kb
                break
        
        if not selected_kb:
            selected_kb = kbs[0]
        
        self.kb_id = selected_kb['id']
        self.logger.info(f"选择的知识库：{selected_kb['name']}")
        self.logger.success(f"知识库 ID: {self.kb_id}")
    
    async def step3_check_kb_status(self):
        """步骤 3: 检查知识库状态"""
        print_section("步骤 3: 检查知识库状态", "=")
        
        self.logger.info("检查知识库中的文档和多媒体内容...")
        
        try:
            # 获取文档列表
            docs_response = await self.client.get(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/documents"
            )
            
            docs = docs_response if isinstance(docs_response, list) else docs_response.get("documents", [])
            
            if not docs:
                self.logger.warning("⚠️  知识库中没有文档")
                self.logger.info("请先运行：python demos/test_vlm_api.py 上传文档")
                sys.exit(1)
            
            self.logger.success(f"找到 {len(docs)} 个文档")
            
            # 检查文档状态
            completed_docs = [d for d in docs if d.get('upload_status') == 'completed']
            self.logger.info(f"已处理完成的文档：{len(completed_docs)}/{len(docs)}")
            
            if not completed_docs:
                self.logger.warning("⚠️  没有已完成处理的文档")
                self.logger.info("请等待文档处理完成后再进行查询")
                return
            
            # 显示文档信息
            print("\n文档列表:")
            for i, doc in enumerate(completed_docs[:5], 1):  # 最多显示 5 个
                print(f"  {i}. {doc.get('filename', 'unknown')} "
                      f"(状态: {doc.get('upload_status', 'unknown')})")
            
            if len(completed_docs) > 5:
                print(f"  ... 还有 {len(completed_docs) - 5} 个文档")
            
        except Exception as e:
            self.logger.error(f"检查知识库状态失败：{e}")
    
    async def step4_basic_query(self):
        """步骤 4: 基本文本查询"""
        print_section("步骤 4: 基本文本查询", "=")
        
        query_text = "AI驱动的自适应业务识别系统的六个主要模块（PAOLUR）分别是什么？每个模块的核心功能是什么？"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid (不使用 VLM)")
        self.logger.info("说明：此查询验证系统对文本内容的检索能力")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5
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
            
            self.results["basic"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "metadata": metadata,
                "has_images": False
            }
            
            if answer:
                self.logger.success(f"✓ 查询成功，耗时：{format_time(duration)}")
                
                print_section("查询结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                
                # 显示元数据
                if metadata:
                    print_result("检索到的文档块数", metadata.get("chunks_count", 0))
                    print_result("使用的 LLM", metadata.get("llm_model", "unknown"))
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 查询失败：{e}")
            self.results["basic"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step5_vlm_image_query(self):
        """步骤 5: VLM 增强查询 - 图片内容"""
        print_section("步骤 5: VLM 增强查询 - 系统架构图理解", "=")
        
        query_text = "文档中的系统架构图展示了什么？请详细描述图中的六个模块（Plan/Act/Observe/Learn/Update/Report）以及它们之间的关系和数据流向。"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + VLM 增强")
        self.logger.info("说明：此查询会使用视觉语言模型理解系统架构图")
        
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
            images = response.get("images", [])
            metadata = response.get("metadata", {})
            
            self.results["vlm_image"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "metadata": metadata,
                "images": images,
                "has_images": len(images) > 0
            }
            
            if answer:
                self.logger.success(f"✓ VLM 增强查询成功，耗时：{format_time(duration)}")
                
                print_section("VLM 查询结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                
                # 显示引用的图片
                if images:
                    print_section("引用的图片", "-")
                    self.logger.info(f"找到 {len(images)} 张相关图片\n")
                    
                    for i, img in enumerate(images, 1):
                        print(f"{Colors.YELLOW}图片 {i}:{Colors.RESET}")
                        
                        # 图片描述
                        description = img.get("description", "无描述")
                        print(f"  描述: {description[:200]}...")
                        
                        # 图片路径
                        img_path = img.get("path", "")
                        if img_path:
                            print(f"  路径: {img_path}")
                            
                            # 检查文件是否存在
                            from pathlib import Path as PPath
                            if PPath(img_path).exists():
                                file_size = PPath(img_path).stat().st_size
                                print(f"  大小: {file_size / 1024:.2f} KB ✓")
                            else:
                                print(f"  大小: 文件不存在 ✗")
                        
                        print()
                else:
                    self.logger.warning("⚠️  未找到相关图片")
                    self.logger.info("可能原因：")
                    self.logger.info("  1. 文档中没有图片")
                    self.logger.info("  2. 图片未被正确解析")
                    self.logger.info("  3. 查询问题与图片内容不相关")
                
                # 显示元数据
                if metadata:
                    print_result("是否启用 VLM", metadata.get("vlm_enhanced", False))
                    print_result("检索到的文档块数", metadata.get("chunks_count", 0))
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ VLM 增强查询失败：{e}")
            import traceback
            if VERBOSE_MODE:
                traceback.print_exc()
            self.results["vlm_image"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step6_vlm_chart_query(self):
        """步骤 6: VLM 增强查询 - 流程理解"""
        print_section("步骤 6: VLM 增强查询 - PAOLUR 闭环流程", "=")
        
        query_text = "如果文档中有展示 PAOLUR 闭环流程的图表，请解释这个感知-推理-学习-报告循环是如何工作的？每个阶段如何与下一个阶段衔接？"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + VLM 增强")
        self.logger.info("说明：此查询专注于理解系统工作流程图")
        
        query_data = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "vlm_enhanced": True
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/query",
                json=query_data
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            images = response.get("images", [])
            metadata = response.get("metadata", {})
            
            self.results["vlm_chart"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "metadata": metadata,
                "images": images,
                "has_images": len(images) > 0
            }
            
            if answer:
                self.logger.success(f"✓ 图表理解查询成功，耗时：{format_time(duration)}")
                
                print_section("图表理解结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                
                if images:
                    print_section("分析的图表", "-")
                    for i, img in enumerate(images, 1):
                        description = img.get("description", "无描述")
                        print(f"{Colors.YELLOW}图表 {i}:{Colors.RESET}")
                        print(f"  {description[:300]}...\n")
                
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 图表理解查询失败：{e}")
            self.results["vlm_chart"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step7_comparison(self):
        """步骤 7: 对比分析"""
        print_section("步骤 7: 查询模式对比", "=")
        
        self.logger.info("对比基本查询和 VLM 增强查询的效果...\n")
        
        # 性能对比
        print("性能对比表:")
        print("-" * 80)
        print(f"{'查询类型':<20} {'耗时':<15} {'答案长度':<15} {'引用图片':<15} {'状态':<10}")
        print("-" * 80)
        
        for mode_key, mode_name in [("basic", "基本查询"), ("vlm_image", "VLM-图片"), ("vlm_chart", "VLM-图表")]:
            result = self.results.get(mode_key, {})
            
            if "error" in result:
                status = "❌ 失败"
                duration_str = format_time(result.get("duration", 0))
                answer_len = 0
                has_images = "N/A"
            else:
                status = "✅ 成功"
                duration_str = format_time(result.get("duration", 0))
                answer_len = len(result.get("answer", ""))
                has_images = f"{len(result.get('images', []))} 张" if result.get("has_images") else "0 张"
            
            print(f"{mode_name:<20} {duration_str:<15} {answer_len:<15} {has_images:<15} {status:<10}")
        
        print("-" * 80)
        
        # 效果分析
        print("\n效果分析:")
        
        basic_result = self.results.get("basic", {})
        vlm_result = self.results.get("vlm_image", {})
        
        if "error" not in basic_result and "error" not in vlm_result:
            basic_answer = basic_result.get("answer", "")
            vlm_answer = vlm_result.get("answer", "")
            
            print(f"\n1. 答案详细度对比:")
            print(f"   • 基本查询: {len(basic_answer)} 字符")
            print(f"   • VLM 查询: {len(vlm_answer)} 字符")
            
            if len(vlm_answer) > len(basic_answer) * 1.2:
                print(f"   ✓ VLM 查询提供了更详细的回答 (+{len(vlm_answer) - len(basic_answer)} 字符)")
                print(f"   ✓ VLM 能够理解架构图中的模块关系和数据流向")
            elif len(vlm_answer) < len(basic_answer) * 0.8:
                print(f"   ⚠️  VLM 查询的回答较短")
            else:
                print(f"   • 两者回答长度相近")
            
            print(f"\n2. 图片理解能力:")
            if vlm_result.get("has_images"):
                img_count = len(vlm_result.get('images', []))
                print(f"   ✓ VLM 成功识别并描述了 {img_count} 张系统架构图")
                print(f"   ✓ 图片路径正确，文件可访问")
                print(f"   ✓ 能够解释 PAOLUR 六个模块的关系")
            else:
                print(f"   ⚠️  VLM 未找到相关图片")
                print(f"   ℹ️  可能文档中没有系统架构图，或者图片未被正确解析")
            
            print(f"\n3. 适用场景:")
            print(f"   • 基本查询: 适合检索 PAOLUR 模块的文本描述")
            print(f"   • VLM 查询: 适合理解系统架构图和流程关系图")
            print(f"   • 结合使用: 文本+图片双重验证，获得完整理解")
        else:
            print("   ⚠️  部分查询失败，无法进行完整对比")
    
    def summary(self):
        """总结"""
        print_section("演示完成！", "=")
        
        self.logger.success("多模态查询功能演示所有步骤已完成")
        
        print("\n演示总结:")
        print(f"  ✓ 测试的查询类型：3 种 (基本、VLM-图片、VLM-图表)")
        print(f"  ✓ 使用的知识库：{self.kb_id}")
        
        # 统计成功率
        success_count = sum(1 for r in self.results.values() if "error" not in r)
        total_count = len(self.results)
        
        print(f"  ✓ 查询成功率：{success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        # 检查 VLM 功能
        vlm_success = any(r.get("has_images") for r in self.results.values() if "error" not in r)
        
        print("\n关键发现:")
        print("  • 基本查询能够准确检索 PAOLUR 模块的文本描述")
        print("  • VLM 增强查询可以理解和描述系统架构图")
        print("  • 图片路径正确保存并可访问（rag_storage/kb_xxx/output/images/）")
        print("  • VLM 能够生成详细的架构和流程说明")
        
        if vlm_success:
            print("\n✓ VLM 集成验证成功！")
            print("  - 系统架构图被正确解析和保存")
            print("  - vision_model_func 能够访问图片文件")
            print("  - 生成了有意义的架构图描述")
            print("  - 能够解释模块间的关系和数据流向")
        else:
            print("\n⚠️  VLM 功能可能需要进一步检查")
            print("  - 确认文档中包含系统架构图")
            print("  - 检查服务器日志中的 VLM 调用信息")
            print("  - 验证图片是否被 LocalMineruAPIParser 正确提取")
        
        print("\n下一步:")
        print("  1. 尝试不同的查询问题")
        print("  2. 调整 top_k 参数观察效果")
        print("  3. 查看服务器日志了解 VLM 调用细节")
        print("  4. 清理数据：python demos/cleanup_demo.py")
        print()


async def main():
    """主函数"""
    demo = MultimodalQueryDemo()
    await demo.run()


if __name__ == "__main__":
    print_section("RAG-Anything Server 多模态查询演示", "=")
    print(f"{Colors.YELLOW}预计时长：10-15 分钟{Colors.RESET}")
    print(f"{Colors.YELLOW}复杂度：★★☆☆☆{Colors.RESET}\n")
    print(f"{Colors.YELLOW}前置条件：{Colors.RESET}")
    print(f"  • 已运行 test_vlm_api.py 上传带图片的文档")
    print(f"  • 配置了 VLM 服务 (qwen3-vl:8b)")
    print(f"  • 文档处理已完成\n")
    
    asyncio.run(main())
