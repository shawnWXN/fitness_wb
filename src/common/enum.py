from enum import IntEnum, Enum


class StaffRoleEnum(IntEnum):
    COACH = 10
    MASTER = 50
    ADMIN = 99


class GenderEnum(Enum):
    UNKNOWN = "0"
    FEMALE = "2"
    MALE = "1"
