"""
完整综合示例 - 第88阶段
端到端业务场景演示
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import time
import uuid

from first_principles_agent import (
    Task, TaskQuartet, FirstPrinciplesAgent, AtomicAction,
    ConfigManager, ConfigItem, ConfigType,
    PermissionManager, Permission, Role, User, ResourceType, PermissionType,
    info, warning, error, debug
)


@dataclass
class BusinessScenario:
    """业务场景"""
    name: str
    description: str
    steps: List[str] = field(default_factory=list)


class ComprehensiveDemo:
    """综合演示"""
    
    def __init__(self):
        self.scenarios: List[BusinessScenario] = []
        self._init_scenarios()
    
    def _init_scenarios(self):
        """初始化演示场景"""
        self.scenarios.extend([
            BusinessScenario(
                name="数据分析工作流",
                description="从原始数据到最终报告的完整分析流程",
                steps=[
                    "数据验证",
                    "数据清洗",
                    "数据转换",
                    "统计分析",
                    "报告生成"
                ]
            ),
            BusinessScenario(
                name="订单处理流程",
                description="从下单到发货的完整订单处理",
                steps=[
                    "订单验证",
                    "库存检查",
                    "支付处理",
                    "订单确认",
                    "发货准备"
                ]
            )
        ])
    
    def run_data_analysis_demo(self) -> Dict[str, Any]:
        """运行数据分析演示"""
        print("="*70)
        print("Demo 1: Data Analysis Workflow")
        print("="*70)
        
        # 1. 创建任务
        quartet = TaskQuartet(
            target="完成数据处理和分析",
            end_rule=lambda ctx: "final_report" in ctx
        )
        
        initial_context = {
            "raw_data": [10, 25, 30, 45, 60, 75, 80, 95],
            "config": {
                "threshold": 50,
                "report_format": "summary"
            }
        }
        
        task = Task("data_analysis", quartet, initial_context)
        
        # 2. 配置Agent
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        # 3. 定义原子动作
        def validate_data(ctx):
            """验证数据完整性"""
            info("Validating data...")
            validated = [x for x in ctx["raw_data"] if isinstance(x, (int, float))]
            return {
                "validated_data": validated,
                "validation_passed": len(validated) == len(ctx["raw_data"])
            }
        
        def clean_data(ctx):
            """清洗和过滤数据"""
            info("Cleaning data...")
            threshold = ctx["config"]["threshold"]
            cleaned = [x for x in ctx["validated_data"] if x > 0]
            return {
                "cleaned_data": cleaned,
                "data_count": len(cleaned)
            }
        
        def analyze_data(ctx):
            """统计分析"""
            info("Analyzing data...")
            data = ctx["cleaned_data"]
            analysis = {
                "count": len(data),
                "sum": sum(data),
                "avg": sum(data) / len(data) if data else 0,
                "max": max(data) if data else 0,
                "min": min(data) if data else 0
            }
            return {"analysis": analysis}
        
        def generate_report(ctx):
            """生成最终报告"""
            info("Generating report...")
            analysis = ctx["analysis"]
            report = {
                "status": "complete",
                "generated_at": time.time(),
                "content": {
                    "analysis": analysis,
                    "summary": f"Processed {analysis['count']} data points, average: {analysis['avg']:.2f}"
                }
            }
            return {"final_report": report}
        
        # 4. 注册动作
        actions = [
            AtomicAction("validate", "数据验证", validate_data),
            AtomicAction("clean", "数据清洗", clean_data),
            AtomicAction("analyze", "数据分析", analyze_data),
            AtomicAction("report", "报告生成", generate_report)
        ]
        agent.set_atomic_actions(actions)
        
        # 5. 执行
        start_time = time.time()
        result = agent.execute()
        end_time = time.time()
        
        # 6. 展示结果
        print("\n" + "="*70)
        print("Execution Summary")
        print("="*70)
        print(f"Success: {result.success}")
        print(f"Duration: {(end_time - start_time) * 1000:.2f}ms")
        
        if result.success:
            final_report = result.context.get("final_report", {})
            print(f"\nFinal Report:")
            print(f"  Status: {final_report.get('status')}")
            content = final_report.get("content", {})
            analysis = content.get("analysis", {})
            print(f"  Analysis Summary:")
            print(f"    Count: {analysis.get('count')}")
            print(f"    Sum: {analysis.get('sum')}")
            print(f"    Average: {analysis.get('avg'):.2f}")
            print(f"    Max: {analysis.get('max')}")
            print(f"    Min: {analysis.get('min')}")
        
        print("="*70 + "\n")
        
        return {
            "success": result.success,
            "result": result,
            "duration_ms": (end_time - start_time) * 1000
        }
    
    def run_order_processing_demo(self) -> Dict[str, Any]:
        """运行订单处理演示"""
        print("="*70)
        print("Demo 2: Order Processing Workflow")
        print("="*70)
        
        # 1. 配置系统
        config_manager = ConfigManager()
        config_manager.register_config_item(ConfigItem(
            key="order.max_quantity",
            type_=ConfigType.INTEGER,
            default=100
        ))
        config_manager.register_config_item(ConfigItem(
            key="order.tax_rate",
            type_=ConfigType.FLOAT,
            default=0.08
        ))
        
        # 2. 设置权限
        permission_manager = PermissionManager()
        user = permission_manager.create_user("demo_user")
        order_perm = Permission(
            name="place_order",
            resource_type=ResourceType.OTHER,
            resource_id="order",
            permission_type=PermissionType.WRITE
        )
        user.add_permission(order_perm)
        
        # 3. 创建订单任务
        quartet = TaskQuartet(
            target="处理订单并完成发货准备",
            end_rule=lambda ctx: "order_ready" in ctx and ctx["order_ready"]
        )
        
        initial_context = {
            "order": {
                "id": f"ORD-{uuid.uuid4().hex[:8]}",
                "items": [
                    {"name": "Product A", "quantity": 2, "price": 25.0},
                    {"name": "Product B", "quantity": 1, "price": 50.0}
                ],
                "customer": "John Doe",
                "shipping_address": "123 Main St"
            },
            "inventory": {"Product A": 100, "Product B": 50, "Product C": 200}
        }
        
        task = Task("order_processing", quartet, initial_context)
        
        # 4. 配置Agent
        agent = FirstPrinciplesAgent()
        agent.set_task(task)
        
        # 5. 定义原子动作
        def validate_order(ctx):
            """验证订单合法性"""
            info("Validating order...")
            order = ctx["order"]
            max_quantity = config_manager.get("order.max_quantity", 100)
            
            total_quantity = sum(item["quantity"] for item in order["items"])
            valid = total_quantity <= max_quantity and total_quantity > 0
            
            return {
                "order_valid": valid,
                "validation_message": "OK" if valid else "Invalid quantity"
            }
        
        def check_inventory(ctx):
            """检查库存"""
            info("Checking inventory...")
            order = ctx["order"]
            inventory = ctx["inventory"]
            
            in_stock = all(
                item["name"] in inventory and inventory[item["name"]] >= item["quantity"]
                for item in order["items"]
            )
            
            return {"inventory_ok": in_stock}
        
        def calculate_total(ctx):
            """计算订单总额"""
            info("Calculating order total...")
            order = ctx["order"]
            tax_rate = config_manager.get("order.tax_rate", 0.08)
            
            subtotal = sum(item["quantity"] * item["price"] for item in order["items"])
            tax = subtotal * tax_rate
            total = subtotal + tax
            
            return {
                "subtotal": subtotal,
                "tax": tax,
                "total": total
            }
        
        def prepare_shipment(ctx):
            """准备发货"""
            info("Preparing shipment...")
            return {
                "order_ready": True,
                "shipping_label": "PRINTED",
                "tracking_number": f"TRK-{uuid.uuid4().hex[:12]}"
            }
        
        # 6. 注册动作
        actions = [
            AtomicAction("validate", "订单验证", validate_order),
            AtomicAction("inventory", "库存检查", check_inventory),
            AtomicAction("calculate", "计算总额", calculate_total),
            AtomicAction("ship", "发货准备", prepare_shipment)
        ]
        agent.set_atomic_actions(actions)
        
        # 7. 执行
        start_time = time.time()
        result = agent.execute()
        end_time = time.time()
        
        # 8. 展示结果
        print("\n" + "="*70)
        print("Execution Summary")
        print("="*70)
        print(f"Success: {result.success}")
        print(f"Duration: {(end_time - start_time) * 1000:.2f}ms")
        
        if result.success:
            order_info = result.context.get("order", {})
            print(f"\nOrder ID: {order_info.get('id')}")
            print(f"Customer: {order_info.get('customer')}")
            print(f"\nItems:")
            for item in order_info.get("items", []):
                print(f"  - {item['name']}: {item['quantity']} x ${item['price']:.2f}")
            
            print(f"\nFinancial:")
            print(f"  Subtotal: ${result.context.get('subtotal', 0):.2f}")
            print(f"  Tax: ${result.context.get('tax', 0):.2f}")
            print(f"  Total: ${result.context.get('total', 0):.2f}")
            
            print(f"\nShipping:")
            print(f"  Status: {result.context.get('shipping_label')}")
            print(f"  Tracking: {result.context.get('tracking_number')}")
        
        print("="*70 + "\n")
        
        return {
            "success": result.success,
            "result": result,
            "duration_ms": (end_time - start_time) * 1000
        }
    
    def run_all_demos(self) -> Dict[str, Any]:
        """运行所有演示"""
        print("\n" + "="*70)
        print("Comprehensive Demo Suite - Stage 88")
        print("="*70 + "\n")
        
        results = {}
        
        # 运行第一个演示
        results["data_analysis"] = self.run_data_analysis_demo()
        
        # 运行第二个演示
        results["order_processing"] = self.run_order_processing_demo()
        
        # 总结
        all_success = all(r["success"] for r in results.values())
        
        print("\n" + "="*70)
        print("Demo Suite Summary")
        print("="*70)
        for demo_name, result in results.items():
            status = "✓ PASSED" if result["success"] else "✗ FAILED"
            print(f"  {demo_name.replace('_', ' ').title()}: {status}")
            print(f"    Duration: {result['duration_ms']:.2f}ms")
        
        print("\nOverall: " + ("✓ ALL DEMOS PASSED" if all_success else "⚠ Some demos failed"))
        print("="*70)
        
        results["all_success"] = all_success
        return results


def create_comprehensive_demo() -> ComprehensiveDemo:
    """创建综合演示"""
    return ComprehensiveDemo()


def run_comprehensive_demo() -> Dict[str, Any]:
    """运行综合演示"""
    demo = create_comprehensive_demo()
    return demo.run_all_demos()
