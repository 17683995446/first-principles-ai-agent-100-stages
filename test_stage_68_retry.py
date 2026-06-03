"""
第68阶段验收测试：任务重试机制与错误恢复策略
测试维度：
1. 重试配置与基础功能
2. 重试策略（各种退避策略）
3. 错误分类
4. 重试管理器功能
5. 恢复检查点管理
"""

import time
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from first_principles_agent import (
    RetryManager, RecoveryManager, RetryConfig, RetryStrategy,
    RetryAttempt, TaskRetryState, RecoveryCheckpoint, ErrorCategory,
    create_retry_config
)


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)


def print_pass(name: str, detail: str = ""):
    """打印通过"""
    message = f"✅ {name}"
    if detail:
        message += f" - {detail}"
    print(message)


def print_fail(name: str, detail: str = ""):
    """打印失败"""
    message = f"❌ {name}"
    if detail:
        message += f" - {detail}"
    print(message)


def test_1_retry_config_basics():
    """测试1：重试配置与基础功能"""
    print_header("测试1：重试配置与基础功能")
    
    try:
        # 创建默认配置
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        print_pass("默认配置正确")
        
        # 创建自定义配置
        config2 = create_retry_config(
            max_attempts=5,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=2.0,
            max_delay=30.0
        )
        assert config2.max_attempts == 5
        assert config2.strategy == RetryStrategy.LINEAR_BACKOFF
        assert config2.base_delay_seconds == 2.0
        print_pass("自定义配置正确")
        
        # 测试可重试和致命错误集合
        assert "timeout" in config.retryable_errors
        assert "validation_error" in config.fatal_errors
        print_pass("错误集合配置正确")
        
        print("\n✅ 测试1通过")
        return True
        
    except Exception as e:
        print_fail("测试1异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_2_retry_strategies():
    """测试2：重试策略（各种退避策略）"""
    print_header("测试2：重试策略（各种退避策略）")
    
    try:
        manager = RetryManager()
        
        # 测试指数退避
        delay1 = manager.calculate_delay(1)
        delay2 = manager.calculate_delay(2)
        delay3 = manager.calculate_delay(3)
        
        # 指数退避应该递增
        assert delay2 >= delay1
        assert delay3 >= delay2
        print_pass(f"指数退避: delay1={delay1:.2f}, delay2={delay2:.2f}, delay3={delay3:.2f}")
        
        # 测试固定延迟（考虑抖动）
        manager.config.strategy = RetryStrategy.FIXED_DELAY
        delay_fixed = manager.calculate_delay(5)
        # 固定延迟应该接近base_delay_seconds（允许抖动范围）
        assert 0.7 * manager.config.base_delay_seconds <= delay_fixed <= 1.3 * manager.config.base_delay_seconds
        print_pass(f"固定延迟策略正确: {delay_fixed:.2f}")
        
        # 测试线性退避（放宽限制，适应抖动）
        manager.config.strategy = RetryStrategy.LINEAR_BACKOFF
        delay_linear1 = manager.calculate_delay(1)
        delay_linear2 = manager.calculate_delay(2)
        delay_linear3 = manager.calculate_delay(3)
        
        # 线性退避应该递增
        assert delay_linear2 >= delay_linear1
        assert delay_linear3 >= delay_linear2
        print_pass(f"线性退避递增: delay1={delay_linear1:.2f}, delay2={delay_linear2:.2f}, delay3={delay_linear3:.2f}")
        
        # 测试立即重试
        manager.config.strategy = RetryStrategy.IMMEDIATE
        delay_immediate = manager.calculate_delay(1)
        assert delay_immediate == 0
        print_pass("立即重试策略正确")
        
        print("\n✅ 测试2通过")
        return True
        
    except Exception as e:
        print_fail("测试2异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_3_error_categorization():
    """测试3：错误分类"""
    print_header("测试3：错误分类")
    
    try:
        manager = RetryManager()
        
        # 测试瞬时错误
        category = manager.categorize_error("Connection timeout error")
        assert category == ErrorCategory.TRANSIENT
        print_pass("瞬时错误分类正确")
        
        # 测试逻辑错误
        category = manager.categorize_error("Invalid input format")
        assert category == ErrorCategory.LOGICAL
        print_pass("逻辑错误分类正确")
        
        # 测试资源错误
        category = manager.categorize_error("Memory allocation failed")
        assert category == ErrorCategory.RESOURCE
        print_pass("资源错误分类正确")
        
        # 测试系统错误
        category = manager.categorize_error("System crash detected")
        assert category == ErrorCategory.SYSTEM
        print_pass("系统错误分类正确")
        
        # 测试未知错误
        category = manager.categorize_error("Some random error")
        assert category == ErrorCategory.UNKNOWN
        print_pass("未知错误分类正确")
        
        # 测试should_retry
        assert manager.should_retry("task1", "Timeout error")
        assert not manager.should_retry("task2", "validation_error occurred")
        assert manager.should_retry("task3", "Network connection failed")
        print_pass("重试判断正确")
        
        print("\n✅ 测试3通过")
        return True
        
    except Exception as e:
        print_fail("测试3异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_4_retry_manager():
    """测试4：重试管理器功能"""
    print_header("测试4：重试管理器功能")
    
    try:
        retry_events = []
        failure_events = []
        
        def on_retry(task_id, attempt, error):
            retry_events.append((task_id, attempt, error))
        
        def on_final_failure(task_id, history):
            failure_events.append((task_id, history))
        
        manager = RetryManager(
            config=create_retry_config(max_attempts=3),
            on_retry=on_retry,
            on_final_failure=on_final_failure
        )
        
        # 安排一个重试
        success = manager.schedule_retry(
            "test_task",
            "Temporary timeout error",
            execution_time_ms=1000
        )
        
        # 应该返回True表示成功安排
        assert success
        print_pass("重试安排成功")
        
        # 获取重试状态
        state = manager.get_retry_state("test_task")
        assert state is not None
        assert state.current_attempt == 1
        assert len(state.retry_history) == 1
        print_pass("重试状态正确")
        
        # 标记成功
        manager.mark_success("test_task")
        state_after = manager.get_retry_state("test_task")
        assert state_after.retry_history[-1].success
        print_pass("成功标记正确")
        
        # 检查统计
        stats = manager.get_stats()
        assert stats["successful_retries"] == 1
        print_pass(f"统计正确: {stats}")
        
        print("\n✅ 测试4通过")
        return True
        
    except Exception as e:
        print_fail("测试4异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_5_recovery_checkpoint():
    """测试5：恢复检查点管理"""
    print_header("测试5：恢复检查点管理")
    
    try:
        recovery = RecoveryManager()
        
        # 保存检查点
        checkpoint_id1 = recovery.save_checkpoint(
            task_id="workflow_1",
            state_data={"progress": 25, "step": "data_loading"},
            completed_steps=["init", "connect"]
        )
        
        checkpoint_id2 = recovery.save_checkpoint(
            task_id="workflow_1",
            state_data={"progress": 50, "step": "processing"},
            completed_steps=["init", "connect", "load"]
        )
        
        print_pass("检查点保存成功")
        
        # 获取最新的检查点
        latest = recovery.get_latest_checkpoint("workflow_1")
        assert latest is not None
        assert latest.state_data["progress"] == 50
        assert "load" in latest.completed_steps
        print_pass("最新检查点获取正确")
        
        # 获取指定的检查点
        specific = recovery.get_checkpoint("workflow_1", checkpoint_id1)
        assert specific is not None
        assert specific.state_data["progress"] == 25
        print_pass("指定检查点获取正确")
        
        # 列出所有检查点
        all_checkpoints = recovery.list_checkpoints("workflow_1")
        assert len(all_checkpoints) == 2
        print_pass("检查点列表正确")
        
        # 删除检查点
        deleted = recovery.delete_checkpoints("workflow_1")
        assert deleted == 2
        assert recovery.get_latest_checkpoint("workflow_1") is None
        print_pass("检查点删除正确")
        
        print("\n✅ 测试5通过")
        return True
        
    except Exception as e:
        print_fail("测试5异常", str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    print_header("第68阶段：任务重试机制与错误恢复策略")
    print("验收标准：完整的重试、退避、错误分类、恢复机制")
    
    all_passed = True
    tests = [
        test_1_retry_config_basics,
        test_2_retry_strategies,
        test_3_error_categorization,
        test_4_retry_manager,
        test_5_recovery_checkpoint
    ]
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 80)
    print("第68阶段验收结果汇总")
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 第68阶段验收通过！")
        print("任务重试机制与错误恢复策略验证通过！")
    else:
        print("\n❌ 第68阶段验收失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
