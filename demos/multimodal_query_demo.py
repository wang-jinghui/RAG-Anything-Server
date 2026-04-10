"""
多模态查询功能演示脚本

时长：10-15 分钟
覆盖内容:
- 使用 /multimodal-query 端点进行多模态查询
- 表格数据查询测试
- 公式查询测试
- 图片路径查询测试

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
            
            # ========== 步骤 4: 表格数据查询 ==========
            await self.step4_table_query()
            
            # ========== 步骤 5: 公式查询 ==========
            await self.step5_equation_query()
            
            # ========== 步骤 6: 图片路径查询 ==========
            await self.step6_image_path_query()
            
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
    
    async def step4_table_query(self):
        """步骤 4: 表格数据查询"""
        print_section("步骤 4: 表格数据查询", "=")
        
        query_text = "比较这些性能指标与文档中提到的方法"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + 多模态内容（表格）")
        self.logger.info("说明：此查询提供表格数据，让系统结合文档内容进行对比分析")
        
        # 构造表格数据
        table_data = """Method,Accuracy,Speed,Memory Usage
LightRAG,95.2%,120ms,2.1GB
GraphRAG,93.8%,180ms,3.5GB
Naive RAG,89.5%,95ms,1.8GB"""
        
        query_payload = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "multimodal_content": [{
                "type": "table",
                "table_data": table_data,
                "table_caption": "不同 RAG 方法的性能对比"
            }]
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/multimodal-query",
                json=query_payload
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            
            self.results["table"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "content_type": "table"
            }
            
            if answer:
                self.logger.success(f"✓ 表格查询成功，耗时：{format_time(duration)}")
                
                print_section("查询结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 表格查询失败：{e}")
            import traceback
            if VERBOSE_MODE:
                traceback.print_exc()
            self.results["table"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step5_equation_query(self):
        """步骤 5: 公式查询"""
        print_section("步骤 5: 公式查询", "=")
        
        query_text = "解释这个公式的物理意义和应用场景"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + 多模态内容（公式）")
        self.logger.info("说明：此查询提供 LaTeX 公式，让系统解释其含义")
        
        query_payload = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "multimodal_content": [{
                "type": "equation",
                "latex": "E = mc^2",
                "equation_caption": "爱因斯坦质能方程"
            }]
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/multimodal-query",
                json=query_payload
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            
            self.results["equation"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "content_type": "equation"
            }
            
            if answer:
                self.logger.success(f"✓ 公式查询成功，耗时：{format_time(duration)}")
                
                print_section("查询结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                
        except Exception as e:
            self.logger.error(f"✗ 公式查询失败：{e}")
            self.results["equation"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step6_image_path_query(self):
        """步骤 6: 图片路径查询"""
        print_section("步骤 6: 图片路径查询", "=")
        
        query_text = "分析这张图片的内容"
        self.logger.info(f"查询问题：{query_text}")
        self.logger.info("查询模式：hybrid + 多模态内容（图片路径）")
        self.logger.info("说明：此查询提供图片路径，让系统理解图片内容")
        
        # 注意：这里需要使用实际存在的图片路径
        # 由于我们不知道具体有哪些图片，这里提供一个示例路径
        # 实际使用时应该从文档中提取真实的图片路径
        image_path = "./rag_storage/kb_test/output/images/test_image.png"
        
        query_payload = {
            "query": query_text,
            "mode": "hybrid",
            "top_k": 5,
            "multimodal_content": [{
                "type": "image",
                "img_path": image_path,
                "image_caption": ["测试图片"]
            }]
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_PREFIX}/knowledge-bases/{self.kb_id}/multimodal-query",
                json=query_payload
            )
            
            duration = time.time() - start_time
            
            answer = response.get("answer", "")
            
            self.results["image"] = {
                "query": query_text,
                "answer": answer,
                "duration": duration,
                "content_type": "image",
                "image_path": image_path
            }
            
            if answer:
                self.logger.success(f"✓ 图片查询成功，耗时：{format_time(duration)}")
                
                print_section("查询结果", "-")
                print(f"{Colors.CYAN}{answer}{Colors.RESET}\n")
                    
            else:
                self.logger.warning("⚠️  查询返回空答案")
                self.logger.info("可能原因：图片路径不存在或无法访问")
                
        except Exception as e:
            self.logger.error(f"✗ 图片查询失败：{e}")
            self.logger.info("提示：图片路径可能不存在，这是预期的")
            self.results["image"] = {"error": str(e), "duration": time.time() - start_time}
    
    async def step7_comparison(self):
        """步骤 7: 对比分析"""
        print_section("步骤 7: 查询模式对比", "=")
        
        self.logger.info("对比不同类型的多模态查询效果...\n")
        
        # 性能对比
        print("性能对比表:")
        print("-" * 70)
        print(f"{'查询类型':<20} {'耗时':<15} {'答案长度':<15} {'状态'}")
        print("-" * 70)
        
        for mode_key, mode_name in [("table", "表格查询"), ("equation", "公式查询"), ("image", "图片查询")]:
            result = self.results.get(mode_key, {})
            
            if "error" in result:
                status = "❌ 失败"
                duration_str = format_time(result.get("duration", 0))
                answer_len = 0
            else:
                status = "✅ 成功"
                duration_str = format_time(result.get("duration", 0))
                answer_len = len(result.get("answer", ""))
            
            print(f"{mode_name:<20} {duration_str:<15} {answer_len:<15} {status}")
        
        print("-" * 70)
        
        # 效果分析
        print("\n效果分析:")
        
        success_count = sum(1 for r in self.results.values() if "error" not in r)
        total_count = len(self.results)
        
        print(f"\n1. 成功率: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        print(f"\n2. 多模态内容支持:")
        if "table" in self.results and "error" not in self.results["table"]:
            print(f"   ✓ 表格查询成功 - 能够处理结构化表格数据")
        else:
            print(f"   ⚠️  表格查询失败")
        
        if "equation" in self.results and "error" not in self.results["equation"]:
            print(f"   ✓ 公式查询成功 - 能够解析和解释 LaTeX 公式")
        else:
            print(f"   ⚠️  公式查询失败")
        
        if "image" in self.results and "error" not in self.results["image"]:
            print(f"   ✓ 图片查询成功 - 能够理解图片内容")
        else:
            print(f"   ℹ️  图片查询跳过或失败（可能需要有效的图片路径）")
        
        print(f"\n3. 适用场景:")
        print(f"   • 表格查询: 适合对比分析结构化数据")
        print(f"   • 公式查询: 适合解释数学公式和科学概念")
        print(f"   • 图片查询: 适合理解图表、架构图等视觉内容")
    
    def summary(self):
        """总结"""
        print_section("演示完成！", "=")
        
        self.logger.success("多模态查询功能演示所有步骤已完成")
        
        print("\n演示总结:")
        print(f"  ✓ 测试的查询类型：3 种 (表格、公式、图片)")
        print(f"  ✓ 使用的知识库：{self.kb_id}")
        
        # 统计成功率
        success_count = sum(1 for r in self.results.values() if "error" not in r)
        total_count = len(self.results)
        
        print(f"  ✓ 查询成功率：{success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        print("\n关键发现:")
        print("  • 多模态查询接口支持表格、公式、图片等多种内容类型")
        print("  • 系统能够将多模态内容与文档知识结合进行分析")
        print("  • 返回纯文本答案，不包含图片元数据")
        print("  • 适用于需要结合外部数据进行查询的场景")
        
        print("\n下一步:")
        print("  1. 尝试不同的多模态内容组合")
        print("  2. 调整 top_k 参数观察效果")
        print("  3. 测试更复杂的表格和公式")
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
    print(f"  • 已启动服务器")
    print(f"  • 配置了 VLM 服务 (qwen3-vl:8b)")
    print(f"  • 知识库中有已处理的文档\n")
    
    asyncio.run(main())
