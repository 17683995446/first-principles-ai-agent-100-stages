
from enum import Enum
from .task_model import Task
from .atomic_converger import AtomicAction
from .topological_decomposer import TaskNode


class VerificationResult(Enum):
    PASSED = "passed"
    FAILED = "failed"


class VerificationType(Enum):
    PRECONDITION = "precondition"
    POSTCONDITION = "postcondition"
    CONSTRAINT = "constraint"
    END_CONDITION = "end_condition"


class VerificationReport:
    def __init__(
        self,
        verification_type,
        result,
        message="",
        details=None
    ):
        self.type = verification_type
        self.result = result
        self.message = message
        self.details = details or {}
        self.timestamp = None
    
    def is_success(self):
        return self.result == VerificationResult.PASSED
    
    def to_dict(self):
        return {
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "result": self.result.value if hasattr(self.result, "value") else str(self.result),
            "message": self.message,
            "details": self.details
        }


class VerificationRule:
    def __init__(
        self,
        rule_id,
        check_func,
        verification_type
    ):
        self.id = rule_id
        self.check_func = check_func
        self.type = verification_type
    
    def apply(self, context):
        try:
            success = self.check_func(context)
            if success:
                return VerificationReport(
                    self.type,
                    VerificationResult.PASSED,
                    f"Rule {self.id} passed"
                )
            else:
                return VerificationReport(
                    self.type,
                    VerificationResult.FAILED,
                    f"Rule {self.id} failed"
                )
        except Exception as e:
            return VerificationReport(
                self.type,
                VerificationResult.FAILED,
                f"Rule {self.id} error: {str(e)}"
            )


class VerificationLayer:
    def __init__(self):
        self.rules = []
        self.reports = []
    
    def add_rule(self, rule):
        self.rules.append(rule)
    
    def check_dependencies_complete(self, node, completed_nodes):
        missing = node.dependencies - completed_nodes
        if missing:
            return VerificationReport(
                VerificationType.PRECONDITION,
                VerificationResult.FAILED,
                f"Missing dependencies: {list(missing)}"
            )
        return VerificationReport(
            VerificationType.PRECONDITION,
            VerificationResult.PASSED,
            "All dependencies satisfied"
        )
    
    def verify_task_preconditions(self, node, context):
        if not node.task.quartet.target:
            return VerificationReport(
                VerificationType.PRECONDITION,
                VerificationResult.FAILED,
                "Task has no target"
            )
        
        if not node.task.quartet.check_preconditions(context):
            return VerificationReport(
                VerificationType.PRECONDITION,
                VerificationResult.FAILED,
                "Preconditions not satisfied"
            )
        
        return VerificationReport(
            VerificationType.PRECONDITION,
            VerificationResult.PASSED,
            "Preconditions satisfied"
        )
    
    def verify_atomic_action_output(self, action, context):
        if action.output is None:
            return VerificationReport(
                VerificationType.POSTCONDITION,
                VerificationResult.FAILED,
                "Action produced no output"
            )
        
        valid, _ = action.validate_output(action.output)
        if not valid:
            return VerificationReport(
                VerificationType.POSTCONDITION,
                VerificationResult.FAILED,
                "Invalid output from action"
            )
        
        return VerificationReport(
            VerificationType.POSTCONDITION,
            VerificationResult.PASSED,
            "Action output valid"
        )
    
    def check_constraints(self, task, context):
        if not task.quartet.check_constraints(context):
            return VerificationReport(
                VerificationType.CONSTRAINT,
                VerificationResult.FAILED,
                "Constraints violated"
            )
        return VerificationReport(
            VerificationType.CONSTRAINT,
            VerificationResult.PASSED,
            "Constraints satisfied"
        )
    
    def check_end_condition(self, task, context):
        if task.quartet.check_end_condition(context):
            return VerificationReport(
                VerificationType.END_CONDITION,
                VerificationResult.PASSED,
                "End condition met"
            )
        return VerificationReport(
            VerificationType.END_CONDITION,
            VerificationResult.FAILED,
            "End condition not met"
        )
    
    def get_reports(self):
        return self.reports.copy()
    
    def get_statistics(self):
        passed = len([r for r in self.reports if r.is_success()])
        failed = len(self.reports) - passed
        return {
            "total": len(self.reports),
            "passed": passed,
            "failed": failed
        }
    
    def reset(self):
        self.reports = []


def create_default_verification_layer():
    return VerificationLayer()
