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


class GenderEnum(Enum):
    UNKNOWN = "0"
    FEMALE = "2"
    MALE = "1"

    explain = {
        UNKNOWN: "未知",
        FEMALE: "女性",
        MALE: "男性"
    }


class BillTypeEnum(Enum):
    DAY = "day"
    COUNT = "count"

    explain = {
        DAY: "计时",
        COUNT: "计次"
    }
