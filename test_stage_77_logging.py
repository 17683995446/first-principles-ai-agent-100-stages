"""
第77阶段验收测试：日志记录与追踪系统
"""

import sys
import time
import threading
from src.first_principles_agent import (
    LogLevel, LogRecord, LogContext,
    LogHandler, ConsoleHandler, MemoryHandler, CallbackHandler,
    Logger, LogManager,
    get_logger, add_default_handler, set_root_level,
    create_context, get_context,
    debug, info, warning, error, critical
)


def test_1_basic_logging():
    """测试1：基础日志记录"""
    print("\n" + "=" * 60)
    print("测试1：基础日志记录")
    print("=" * 60)

    logger = Logger("test_logger")
    memory_handler = MemoryHandler(level=LogLevel.DEBUG)
    logger.add_handler(memory_handler)

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    records = memory_handler.get_records()
    assert len(records) == 5

    assert records[0].level == LogLevel.DEBUG
    assert records[0].message == "Debug message"

    assert records[4].level == LogLevel.CRITICAL
    assert records[4].message == "Critical message"

    print(f"  ✓ 记录了 {len(records)} 条日志")
    for r in records:
        print(f"    - {r.format()}")

    print("\n✅ 测试1通过：基础日志记录功能正常")
    return True


def test_2_log_levels():
    """测试2：日志级别过滤"""
    print("\n" + "=" * 60)
    print("测试2：日志级别过滤")
    print("=" * 60)

    logger = Logger("level_test")
    memory_handler = MemoryHandler(level=LogLevel.WARNING)
    logger.add_handler(memory_handler)
    logger.set_level(LogLevel.WARNING)

    logger.debug("Should not show")
    logger.info("Should not show")
    logger.warning("Should show")
    logger.error("Should show")
    logger.critical("Should show")

    records = memory_handler.get_records()
    assert len(records) == 3
    assert records[0].level == LogLevel.WARNING
    assert records[2].level == LogLevel.CRITICAL

    print(f"  ✓ 仅记录 WARNING 及以上级别，共 {len(records)} 条")
    for r in records:
        print(f"    - {r.format()}")

    print("\n✅ 测试2通过：日志级别过滤功能正常")
    return True


def test_3_context_tracing():
    """测试3：上下文追踪"""
    print("\n" + "=" * 60)
    print("测试3：上下文追踪")
    print("=" * 60)

    logger = Logger("trace_test")
    memory_handler = MemoryHandler(level=LogLevel.DEBUG)
    logger.add_handler(memory_handler)

    context = logger.create_context("test-trace-123")
    context.set("user_id", "u_456")
    context.set("request_id", "req_789")

    logger.info("Processing request")

    records = memory_handler.get_records()
    assert len(records) == 1
    assert records[0].trace_id == "test-trace-123"
    assert records[0].context.get("user_id") == "u_456"
    assert records[0].context.get("request_id") == "req_789"

    print(f"  ✓ 上下文追踪正常，trace_id={records[0].trace_id}")
    print(f"  ✓ 上下文信息：{records[0].context}")

    logger.clear_context()
    logger.info("No context message")
    assert len(memory_handler.get_records()) == 2

    print("\n✅ 测试3通过：上下文追踪功能正常")
    return True


def test_4_context_api():
    """测试4：上下文API"""
    print("\n" + "=" * 60)
    print("测试4：上下文API")
    print("=" * 60)

    context = LogContext(trace_id="api-test")
    context.set("key1", "value1")
    context.set("key2", "value2")

    assert context.get("key1") == "value1"
    assert context.get("key2") == "value2"

    context.update(key1="new_value1", key3="value3")
    assert context.get("key1") == "new_value1"
    assert context.get("key3") == "value3"

    context.remove("key2")
    assert context.get("key2") is None

    context.clear()
    assert context.get("key1") is None

    print("  ✓ 上下文API功能正常")
    print("\n✅ 测试4通过：上下文API功能正常")
    return True


def test_5_callback_handler():
    """测试5：回调处理器"""
    print("\n" + "=" * 60)
    print("测试5：回调处理器")
    print("=" * 60)

    received_records = []

    def callback(record):
        received_records.append(record)

    logger = Logger("callback_test")
    callback_handler = CallbackHandler(callback, level=LogLevel.INFO)
    logger.add_handler(callback_handler)

    logger.info("First message")
    logger.warning("Second message")

    assert len(received_records) == 2
    assert received_records[0].message == "First message"
    assert received_records[1].message == "Second message"

    print(f"  ✓ 回调收到 {len(received_records)} 条记录")

    print("\n✅ 测试5通过：回调处理器功能正常")
    return True


def test_6_global_api():
    """测试6：全局API"""
    print("\n" + "=" * 60)
    print("测试6：全局API")
    print("=" * 60)

    memory_handler = MemoryHandler(level=LogLevel.DEBUG)
    add_default_handler(memory_handler)

    debug("Global debug")
    info("Global info")

    records = memory_handler.get_records()
    assert len(records) >= 2

    context = create_context("global-trace")
    context.set("service", "auth")

    info("With global context")

    records_with_context = [
        r for r in memory_handler.get_records()
        if r.trace_id == "global-trace"
    ]
    assert len(records_with_context) >= 1

    print(f"  ✓ 全局API正常，记录了 {len(records)} 条日志")
    print(f"  ✓ 上下文追踪正常")

    print("\n✅ 测试6通过：全局API功能正常")
    return True


def test_7_multiple_handlers():
    """测试7：多个处理器"""
    print("\n" + "=" * 60)
    print("测试7：多个处理器")
    print("=" * 60)

    logger = Logger("multi_test")

    handler1 = MemoryHandler(level=LogLevel.DEBUG)
    handler2 = MemoryHandler(level=LogLevel.ERROR)

    logger.add_handler(handler1)
    logger.add_handler(handler2)

    logger.debug("Debug only in handler1")
    logger.error("Error in both handlers")

    assert len(handler1.get_records()) == 2
    assert len(handler2.get_records()) == 1

    print(f"  ✓ 处理器1：{len(handler1.get_records())} 条")
    print(f"  ✓ 处理器2：{len(handler2.get_records())} 条")

    print("\n✅ 测试7通过：多个处理器功能正常")
    return True


def run_all_tests():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("第77阶段验收测试：日志记录与追踪系统")
    print("=" * 60)

    tests = [
        test_1_basic_logging,
        test_2_log_levels,
        test_3_context_tracing,
        test_4_context_api,
        test_5_callback_handler,
        test_6_global_api,
        test_7_multiple_handlers
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试失败：{test.__name__}")
            print(f"   错误：{e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果：{passed}/{len(tests)} 通过")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有验收测试通过！第77阶段完成！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
