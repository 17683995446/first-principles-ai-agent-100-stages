"""
任务解析与建模模块
第22-30阶段实现
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import uuid
from .task_model import (
    Task,
    TaskQuartet,
    EndRule,
    Constraint,
    Precondition,
    ConstraintType,
    ValidationError
)


class TaskParser:
    """
    用户需求统一解析入口
    第22阶段实现
    """
    
    def __init__(self):
        self.vague_patterns = [
            "随便", "等等", "看看", "弄一下", "搞一下",
            "帮我", "给我", "处理一下", "搞一搞"
        ]
        self.ambiguous_keywords = [
            "优化", "改进", "完善", "调整", "处理"
        ]
    
    def parse(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Task, List[str]]:
        """
        统一解析入口
        
        Args:
            user_input: 用户自然语言输入
            context: 初始上下文
        
        Returns:
            Tuple[是否成功, 解析得到的Task, 警告列表]
        """
        warnings = []
        
        # 基本验证
        if not user_input or len(user_input.strip()) < 2:
            return False, None, ["Input too short"]
        
        # 歧义检测
        ambiguity_warnings = self.detect_ambiguity(user_input)
        warnings.extend(ambiguity_warnings)
        
        # 目标提取
        target = self.extract_target(user_input)
        
        # 创建任务
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            quartet=TaskQuartet(target=target),
            context=context or {}
        )
        
        return True, task, warnings
    
    def detect_ambiguity(self, text: str) -> List[str]:
        """检测歧义"""
        warnings = []
        
        for pattern in self.vague_patterns:
            if pattern in text:
                warnings.append(f"Detected vague expression: '{pattern}'")
        
        for keyword in self.ambiguous_keywords:
            if keyword in text:
                warnings.append(f"Ambiguous keyword: '{keyword}' - consider being more specific")
        
        return warnings
    
    def extract_target(self, text: str) -> str:
        """提取目标"""
        # 移除语气词和助词
        cleaned = text.strip()
        for phrase in ["帮我", "请帮我", "能不能帮我", "请"]:
            if cleaned.startswith(phrase):
                cleaned = cleaned[len(phrase):]
        
        return cleaned


class TargetExtractor:
    """
    Target 提取与归一化
    第23阶段实现
    """
    
    def __init__(self):
        self.redundant_words = [
            "快速", "高效", "简单", "方便", "顺便"
        ]
    
    def extract(self, raw_input: str) -> str:
        """
        提取唯一目标
        
        Args:
            raw_input: 原始输入
        
        Returns:
            归一化后的目标字符串
        """
        # 步骤1: 清理语气词
        target = self._remove_redundancy(raw_input)
        
        # 步骤2: 歧义剔除
        target = self._resolve_ambiguity(target)
        
        # 步骤3: 归一化
        target = self._normalize(target)
        
        return target
    
    def _remove_redundancy(self, text: str) -> str:
        """移除冗余词"""
        result = text
        for word in self.redundant_words:
            result = result.replace(word, "")
        return result.strip()
    
    def _resolve_ambiguity(self, text: str) -> str:
        """歧义剔除"""
        # 替换模糊表达
        replacements = {
            "搞一下": "执行",
            "弄一下": "执行",
            "看看": "检查",
            "等等": ""
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result.strip()
    
    def _normalize(self, text: str) -> str:
        """归一化"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class PreconditionRecognizer:
    """
    前置条件自动识别
    第24阶段实现
    """
    
    def recognize(self, task_description: str, context: Dict[str, Any]) -> List[Precondition]:
        """
        自动识别前置条件
        
        Args:
            task_description: 任务描述
            context: 当前上下文
        
        Returns:
            识别到的前置条件列表
        """
        preconditions = []
        
        # 文件相关
        if "读取" in task_description or "读取文件" in task_description:
            preconditions.append(Precondition(
                check_func=lambda ctx: "file_path" in ctx,
                description="需要文件路径"
            ))
        
        # 数据库相关
        if "数据库" in task_description or "查询" in task_description:
            preconditions.append(Precondition(
                check_func=lambda ctx: ctx.get("db_connected", False),
                description="需要数据库连接"
            ))
        
        # API 相关
        if "API" in task_description or "接口" in task_description:
            preconditions.append(Precondition(
                check_func=lambda ctx: "api_key" in ctx or "endpoint" in ctx,
                description="需要API配置"
            ))
        
        return preconditions


class BoundaryRecognizer:
    """
    边界约束识别与写入
    第25阶段实现
    """
    
    def recognize(self, task_description: str) -> List[Constraint]:
        """
        自动识别边界约束
        
        Args:
            task_description: 任务描述
        
        Returns:
            识别到的约束列表
        """
        constraints = []
        
        # 步骤数限制
        if "最多" in task_description and "步" in task_description:
            match = re.search(r"最多(\d+)步", task_description)
            if match:
                max_steps = int(match.group(1))
                constraints.append(Constraint(
                    constraint_type=ConstraintType.MAX_STEPS,
                    value=max_steps,
                    description=f"最多{max_steps}步"
                ))
        
        # 时间限制
        if "分钟内" in task_description:
            match = re.search(r"(\d+)分钟", task_description)
            if match:
                minutes = int(match.group(1))
                constraints.append(Constraint(
                    constraint_type=ConstraintType.TIME_LIMIT,
                    value=minutes * 60,
                    description=f"时间限制: {minutes}分钟"
                ))
        
        # 网络限制
        if "不联网" in task_description or "离线" in task_description:
            constraints.append(Constraint(
                constraint_type=ConstraintType.NETWORK_RESTRICTED,
                value=True,
                description="禁止网络访问"
            ))
        
        return constraints


class EndRuleParser:
    """
    EndRule 机器可判定终止规则解析器
    第26阶段实现
    """
    
    def parse(self, end_description: str, context: Dict[str, Any]) -> Optional[EndRule]:
        """
        解析终止规则
        
        Args:
            end_description: 终止条件描述
            context: 上下文
        
        Returns:
            EndRule 实例或None
        """
        # 基于关键词的规则生成
        if "完成" in end_description or "结束" in end_description:
            return EndRule(
                end_func=lambda ctx: ctx.get("completed", False),
                description="任务完成标记"
            )
        
        if "文件" in end_description:
            file_pattern = re.search(r"['\"](.+?)['\"]", end_description)
            if file_pattern:
                filename = file_pattern.group(1)
                return EndRule(
                    end_func=lambda ctx, f=filename: f in ctx.get("files", []),
                    description=f"文件{f}存在"
                )
        
        if "结果" in end_description:
            return EndRule(
                end_func=lambda ctx: "result" in ctx,
                description="结果已生成"
            )
        
        # 默认终止规则
        return EndRule(
            end_func=lambda ctx: False,
            description="默认终止规则（需要手动设置）"
        )
    
    def create_simple_end_rule(self, check_field: str) -> EndRule:
        """
        创建简单的字段检查终止规则
        
        Args:
            check_field: 要检查的字段名
        
        Returns:
            EndRule实例
        """
        return EndRule(
            end_func=lambda ctx, field=check_field: field in ctx and ctx[field] is not None,
            description=f"检查字段: {check_field}"
        )


class TaskValidator:
    """
    任务整体合法性校验接口
    第27阶段实现
    """
    
    def __init__(self):
        self.parser = TaskParser()
        self.target_extractor = TargetExtractor()
    
    def validate(self, task: Task) -> Tuple[bool, List[ValidationError]]:
        """
        全面校验任务合法性
        
        Args:
            task: 要校验的任务
        
        Returns:
            Tuple[是否合法, 错误列表]
        """
        errors = []
        
        # 1. 基本验证
        is_valid, basic_errors, _ = task.validate()
        errors.extend([ValidationError(e.field, e.message) for e in basic_errors])
        
        # 2. Target 质量检查
        if task.quartet.target:
            if len(task.quartet.target) < 5:
                errors.append(ValidationError(
                    "target",
                    "Target too short, please be more specific"
                ))
            
            # 检查模糊表达
            for pattern in self.parser.vague_patterns:
                if pattern in task.quartet.target:
                    errors.append(ValidationError(
                        "target",
                        f"Target contains vague expression: '{pattern}'"
                    ))
        
        # 3. 前置条件检查
        for pc in task.quartet.preconditions:
            if pc.required:
                if not callable(pc.check_func):
                    errors.append(ValidationError(
                        "precondition",
                        "Precondition check function not callable"
                    ))
        
        # 4. 约束检查
        for c in task.quartet.constraints:
            if not c.enabled:
                continue
            if c.value is None:
                errors.append(ValidationError(
                    "constraint",
                    f"Constraint {c.type.value} has no value"
                ))
        
        # 5. 终止规则检查
        if task.quartet.end_rule is None:
            errors.append(ValidationError(
                "end_rule",
                "No end rule defined - task may never complete"
            ))
        elif not callable(task.quartet.end_rule.end_func):
            errors.append(ValidationError(
                "end_rule",
                "End rule function not callable"
            ))
        
        return len(errors) == 0, errors
    
    def quick_check(self, task: Task) -> bool:
        """
        快速检查
        
        Args:
            task: 任务
        
        Returns:
            是否可能合法
        """
        return (
            task.quartet.target is not None and
            len(task.quartet.target) >= 2
        )


class TaskRejector:
    """
    无效任务拦截与标准化拒绝反馈
    第28阶段实现
    """
    
    REJECT_REASONS = {
        "EMPTY_INPUT": "输入为空或过短",
        "VAGUE_TARGET": "目标描述模糊",
        "NO_END_RULE": "缺少终止规则",
        "HARMFUL_CONTENT": "包含禁止内容",
        "OUT_OF_SCOPE": "超出系统能力范围"
    }
    
    def should_reject(self, task: Task) -> Tuple[bool, str]:
        """
        判断是否应拒绝任务
        
        Args:
            task: 任务
        
        Returns:
            Tuple[是否拒绝, 拒绝原因]
        """
        # 空输入检查
        if not task.quartet.target or len(task.quartet.target.strip()) < 2:
            return True, self.REJECT_REASONS["EMPTY_INPUT"]
        
        # 模糊目标检查
        vague_patterns = ["随便", "等等", "看看", "弄一下"]
        for pattern in vague_patterns:
            if pattern in task.quartet.target:
                return True, self.REJECT_REASONS["VAGUE_TARGET"]
        
        # 无终止规则检查
        if task.quartet.end_rule is None:
            return True, self.REJECT_REASONS["NO_END_RULE"]
        
        # 危害内容检查（示例）
        harmful_keywords = ["删除所有文件", "格式化硬盘"]
        for keyword in harmful_keywords:
            if keyword in task.quartet.target.lower():
                return True, self.REJECT_REASONS["HARMFUL_CONTENT"]
        
        return False, ""
    
    def create_rejection_response(self, reason_code: str, task: Task) -> Dict[str, Any]:
        """
        创建标准化拒绝响应
        
        Args:
            reason_code: 拒绝原因代码
            task: 被拒绝的任务
        
        Returns:
            拒绝响应字典
        """
        return {
            "accepted": False,
            "reason_code": reason_code,
            "reason_message": self.REJECT_REASONS.get(reason_code, "Unknown reason"),
            "task_id": task.id,
            "suggestions": self._generate_suggestions(reason_code)
        }
    
    def _generate_suggestions(self, reason_code: str) -> List[str]:
        """生成改进建议"""
        suggestions = {
            "EMPTY_INPUT": [
                "请提供更详细的任务描述",
                "说明您希望达到的具体目标"
            ],
            "VAGUE_TARGET": [
                "请明确要做什么",
                "提供具体的操作对象和期望结果"
            ],
            "NO_END_RULE": [
                "请定义任务完成的标准",
                "说明如何判断任务已完成"
            ],
            "HARMFUL_CONTENT": [
                "此操作被系统拒绝",
                "请选择其他安全的操作方式"
            ],
            "OUT_OF_SCOPE": [
                "当前系统不支持此操作",
                "请尝试其他类型的任务"
            ]
        }
        return suggestions.get(reason_code, ["请重新输入任务描述"])


class UnifiedTaskModeling:
    """
    统一任务建模入口
    整合第22-28阶段功能
    """
    
    def __init__(self):
        self.parser = TaskParser()
        self.target_extractor = TargetExtractor()
        self.precondition_recognizer = PreconditionRecognizer()
        self.boundary_recognizer = BoundaryRecognizer()
        self.endrule_parser = EndRuleParser()
        self.validator = TaskValidator()
        self.rejector = TaskRejector()
    
    def model(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        统一建模入口
        
        Args:
            user_input: 用户输入
            context: 初始上下文
        
        Returns:
            Tuple[是否成功, 结果字典]
        """
        result = {
            "success": False,
            "task": None,
            "errors": [],
            "warnings": [],
            "rejected": False,
            "rejection_info": None
        }
        
        # 1. 解析输入
        parse_success, task, warnings = self.parser.parse(user_input, context)
        if not parse_success:
            result["errors"].append("Parse failed")
            return False, result
        
        result["warnings"].extend(warnings)
        
        # 2. Target 提取归一化
        task.quartet.target = self.target_extractor.extract(task.quartet.target)
        
        # 3. 自动识别前置条件
        preconditions = self.precondition_recognizer.recognize(
            task.quartet.target,
            context or {}
        )
        task.quartet.preconditions.extend(preconditions)
        
        # 4. 自动识别约束
        constraints = self.boundary_recognizer.recognize(task.quartet.target)
        task.quartet.constraints.extend(constraints)
        
        # 5. 自动添加默认 EndRule（如果用户没有提供）
        if task.quartet.end_rule is None:
            task.quartet.end_rule = EndRule(
                end_func=lambda ctx: ctx.get("completed", False),
                description="默认终止规则：等待completed标志"
            )
        
        # 6. 拒绝检查
        should_reject, reason = self.rejector.should_reject(task)
        if should_reject:
            result["rejected"] = True
            result["rejection_info"] = self.rejector.create_rejection_response(reason, task)
            return False, result
        
        # 7. 合法性校验
        is_valid, errors = self.validator.validate(task)
        if not is_valid:
            result["errors"].extend([e.message for e in errors])
            return False, result
        
        result["success"] = True
        result["task"] = task
        
        return True, result
    
    def model_with_end_rule(self, user_input: str, end_description: str, context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        带终止规则的建模
        
        Args:
            user_input: 用户输入
            end_description: 终止条件描述
            context: 初始上下文
        
        Returns:
            Tuple[是否成功, 结果字典]
        """
        # 基本建模
        success, result = self.model(user_input, context)
        
        if not success:
            return False, result
        
        # 添加终止规则
        end_rule = self.endrule_parser.parse(end_description, context or {})
        result["task"].quartet.end_rule = end_rule
        
        # 重新校验
        is_valid, errors = self.validator.validate(result["task"])
        if not is_valid:
            result["success"] = False
            result["errors"].extend([e.message for e in errors])
            return False, result
        
        return True, result
