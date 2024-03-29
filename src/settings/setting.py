import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


@dataclass
class _SETTING:
    DEV: bool = field(default=False)
    MYSQL_URI: str = field(default='mysql://*:*@*:*/fitness_db')
    LOG_LEVEL: str = field(default='INFO')

    def __post_init__(self):
        for attr, _field in self.__dataclass_fields__.items():  # noqa
            env_value = os.getenv(attr)
            if env_value is not None:
                # 根据字段类型转换环境变量值
                setattr(self, attr, self._convert_type(_field.type, env_value))

    @staticmethod
    def _convert_type(field_type, env_value):
        if field_type == bool:
            return env_value.lower() in ('true', '1', 'yes')
        elif field_type == int:
            return int(env_value)
        # 添加其他类型转换逻辑（如果需要）
        return env_value


SETTING = _SETTING()
