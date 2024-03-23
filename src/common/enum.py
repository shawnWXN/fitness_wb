from enum import Enum


class StaffRoleEnum(Enum):
    COACH = 10
    MASTER = 50
    ADMIN = 99

    explain = {
        COACH: "教练",
        MASTER: "店主",
        ADMIN: "管理员"
    }

    iter = [
        COACH,
        MASTER,
        ADMIN
    ]


class BillTypeEnum(Enum):
    DAY = "day"
    COUNT = "count"

    explain = {
        DAY: "计时",
        COUNT: "计次"
    }

    iter = [
        DAY,
        COUNT,
    ]


class OrderStatusEnum(Enum):
    # PENDING = "pending"
    # REJECT = "reject"
    ACTIVATED = "activated"
    EXPIRED = "expired"
    REFUND = "refund"

    explain = {
        # PENDING: "待审核",
        # REJECT: "审核拒绝",
        ACTIVATED: "审核通过",
        EXPIRED: "已过期",
        REFUND: "已退款"
    }

    iter = [
        # PENDING,
        # REJECT,
        ACTIVATED,
        EXPIRED,
        REFUND
    ]


class ExpenseStatusEnum(Enum):
    PENDING = "pending"
    REJECT = "reject"
    ACTIVATED = "activated"
    FREE = "free"

    explain = {
        PENDING: "待审核",
        REJECT: "审核拒绝",
        ACTIVATED: "审核通过",
        FREE: "赠送"
    }

    iter = [
        PENDING,
        REJECT,
        ACTIVATED,
        FREE
    ]
