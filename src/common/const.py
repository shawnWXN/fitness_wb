# -*- coding:utf-8 -*-
class _Const(object):
    def __setattr__(self, *_):
        raise SyntaxError('Trying to change a constant value')

    SYSTEM_NAME = "fitness"
    SUB_SYSTEM_NAME = "wb"

    SYSTEM_SESSIONS_PREFIX = f"{SYSTEM_NAME}_{SUB_SYSTEM_NAME}:sessions"
    SYSTEM_SESSIONS_MAP = f"{SYSTEM_NAME}_{SUB_SYSTEM_NAME}:sessions:map"

    MAX_BACK_FILE_NUM = 10
    MAX_BACK_FILE_SIZE = 32 * 1024 * 1024

    SYSTEM_APP_NAME = '__' + SYSTEM_NAME.upper() + '_' + \
                      SUB_SYSTEM_NAME.upper() + '_NODE__'

    URL_PREFIX = '/' + SYSTEM_NAME + '/' + SUB_SYSTEM_NAME

    BOOL_TRUE = 'true'
    BOOL_FALSE = 'false'
    CODE_UTF8 = 'utf-8'
    UTF_8 = 'utf8'

    STAT_KEY = 'key'
    STAT_VALUE = 'value'

    TOKEN = 'token'

    MESSAGE = 'message'
    SUCCESS = 'success'
    FAILURE = 'failure'
    ERROR_CODE = 'error_code'
    REASON = 'reason'
    DATA = 'data'
    LIST = 'list'
    COUNT = 'count'

    CIPHER_KEY = "rRT69TMmoQDNFmGypVYzkYtdK62DRSo9hrb1tpB78jQ="

    # json schema
    TYPE = 'type'
    OBJECT = 'object'
    STRING = 'string'
    INTEGER = 'integer'
    NUMBER = 'number'
    BOOLEAN = "boolean"
    ARRAY = 'array'
    NULL = 'null'

    SCHEMA_CONST = 'const'
    REQUIRED = 'required'
    TITLE = 'title'
    DESCRIPTION = 'description'
    ADDITIONAL_PROPERTIES = 'additionalProperties'
    MAX_PROPERTIES = 'maxProperties'
    MIN_PROPERTIES = 'minProperties'
    PROPERTIES = 'properties'
    ENUM = 'enum'
    ITEMS = 'items'
    MINITEMS = 'minItems'
    MAXITEMS = 'maxItems'
    PATTERN = 'pattern'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'
    TIMESTAMP = 'timestamp'
    MIN_LENGTH = 'minLength'
    MAX_LENGTH = 'maxLength'
    DESC = "desc"
    ASC = "asc"
    ALLOF = 'allOf'
    ANYOF = 'anyOf'
    ONEOF = 'oneOf'
    EXCLUSIVE_MINIMUM = "exclusiveMinimum"
    EXCLUSIVE_MAXIMUM = "exclusiveMaximum"
    ERR_MSG = 'err_msg'

    COACH_ID = 'coach_id'
    COACH_NAME = 'coach_name'
    BILL_TYPE = 'bill_type'
    LIMIT_DAYS = 'limit_days'
    LIMIT_COUNTS = 'limit_counts'

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT = '%Y-%m-%d'

    # error response definition
    SYSTEM_ERROR_CODE = 50001
    SYSTEM_ERROR_MSG = '系统发生异常'

    AUTH_INVALID_CODE = 50002
    AUTH_INVALID_MSG = '用户认证失败'

    BODY_NONE_CODE = 50003
    BODY_NONE_MSG = '请求体为空'

    OPERATION_FAILURE_CODE = 50004
    OPERATION_FAILURE_MSG = '操作失败'

    SESSION_ID = "session_id"

    ID = "id"
    COURSE_ID = "course_id"
    COURSE_NAME = "course_name"

    MEMBER_ID = "member_id"
    MEMBER_NAME = "member_name"

    EXPIRE_TIME = 'expire_time'
    SURPLUS_COUNTS = 'surplus_counts'
    COMMENTS = 'comments'
    COMMENT = 'comment'
    ORDER_NO = 'order_no'

    ROLE = "role"

    IS_ACTIVE = "is_active"

    STATUS = "status"
    TRUE_STATUS = "T"
    FALSE_STATUS = "F"

    CREATE_DATE_START = 'create_date_start'
    CREATE_DATE_END = 'create_date_end'

    CREATE_TIME = 'create_time'
    UPDATE_TIME = 'update_time'
    OP = 'op'
    ALLOT = 'allot'
    BACK = 'back'
    DEL = 'del'
    SEAS_OP_ENUM = [ALLOT, BACK, DEL]
    SEARCH = 'search'
    STAFF_ROLES = 'staff_roles'
    PAGE_SIZE = 'page_size'
    PAGE_NUM = 'page_num'

    CNAME = 'cname'
    BRAND = 'brand'
    PUBLIC = 'public'
    PRIVATE = 'private'

    USER_NAME = 'user_name'
    NICK_NAME = 'nick_name'
    PASSWD = 'passwd'

    SCHEMA = 'schema'
    DOMAIN = 'domain'
    CONTACT_NAME = 'contact_name'
    CONTACT_POSITION = 'contact_position'
    QQ = 'qq'
    WECHAT = 'wechat'
    EMAIL = 'email'
    PHONE = 'phone'

    ALLOT_GAP = 'allot_gap'

    C_ID = 'c_id'
    U_ID = 'u_id'
    CONTENT = 'content'
    JOURNAL = 'journal'


CONST = _Const()
