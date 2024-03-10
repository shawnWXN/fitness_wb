import datetime
import time

from common.const import CONST


def get_date_str(date_time):
    if not date_time:
        return None

    data_time_str = date_time.strftime(CONST.DATE_FORMAT)
    return data_time_str


def get_today_date():
    date_now = datetime.datetime.now()
    return get_date_str(date_now)


def get_date_time_str(date_time):
    if not date_time:
        return None

    data_time_str = date_time.strftime(CONST.DATETIME_FORMAT)
    return data_time_str


def get_today_date_time():
    date_now = datetime.datetime.now()
    return get_date_time_str(date_now)


def minus_day_hour(start_date, end_date):
    if isinstance(start_date, datetime.datetime):
        start_time = start_date
    else:
        start_time = datetime.datetime.strptime(start_date, CONST.DATETIME_FORMAT)

    if isinstance(end_date, datetime.datetime):
        end_time = end_date
    else:
        end_time = datetime.datetime.strptime(end_date, CONST.DATETIME_FORMAT)

    days = (end_time - start_time).days
    seconds = (end_time - start_time).seconds
    return days, seconds // 3600


def minus_day(start_date, end_date):
    start_time = datetime.datetime.strptime(start_date, CONST.DATE_FORMAT)
    end_time = datetime.datetime.strptime(end_date, CONST.DATE_FORMAT)
    days = (end_time - start_time).days
    return days


def less(src_date, dst_date, padding=0):
    minus = minus_day(dst_date, src_date) + padding
    if minus >= 0:
        return False

    return True


def get_timestamp():
    return int(round(time.time()))


def get_date_time(date_str):
    if not date_str:
        return None

    date_time = datetime.datetime.strptime(date_str, CONST.DATE_FORMAT)
    return date_time


def get_data_time_str(date_time):
    if not date_time:
        return None

    data_time_str = date_time.strftime(CONST.DATE_FORMAT)
    return data_time_str


def get_next_date_str(date_str):
    date_time = get_date_time(date_str)
    pre_date_time = date_time + datetime.timedelta(days=1)
    data_time_str = pre_date_time.strftime(CONST.DATE_FORMAT)
    return data_time_str


def get_pre_date_str(date_str):
    date_time = get_date_time(date_str)
    pre_date_time = date_time + datetime.timedelta(days=-1)
    data_time_str = pre_date_time.strftime(CONST.DATE_FORMAT)
    return data_time_str


def get_first_date(date_str):
    date_time = get_date_time(date_str)
    first_day = datetime.date(date_time.year, date_time.month, 1)
    return first_day


def get_first_date_str(date_str):
    first_day = get_first_date(date_str)
    first_day_str = get_data_time_str(first_day)
    return first_day_str


def get_last_day_date(date_str=None):
    if date_str:
        date_time = get_date_time(date_str)
    else:
        date_time = datetime.datetime.now()

    last_day = date_time + datetime.timedelta(days=-1)
    return get_data_time_str(last_day)


def less_equal(src_date, dst_date, padding=0):
    minus = minus_day(src_date, dst_date) + padding
    if minus <= 0:
        return True

    return False


def is_weekend(date_str):
    week_day = get_date_time(date_str).strftime(CONST.WEEK_DATE_FORMAT)
    if week_day == CONST.WEEK_END_DAY:
        return True

    return False


def str_time_delta(src_date, days=1):
    if not src_date:
        return None

    str_time_str = get_date_time_by_str(src_date)
    dst_time = str_time_str + datetime.timedelta(days=days)
    dst_time_str = get_date_time_str(dst_time)
    return dst_time_str


def str_date_delta(src_date, days=1):
    if not src_date:
        return None

    src_date_time = get_date_time(src_date)
    dst_time = src_date_time + datetime.timedelta(days=days)
    dst_time_str = get_data_time_str(dst_time)
    return dst_time_str


def get_week_end_date(date_str):
    week_day = get_date_time(date_str).strftime(CONST.WEEK_DATE_FORMAT)
    delta_day = CONST.TOTAL_WEEK_DAYS - int(week_day) - 1
    week_end_date = str_date_delta(date_str, delta_day)
    return week_end_date


def get_month_date(src_date):
    return get_date_time(src_date).strftime(CONST.MONTH_DATE_FORMAT)


def is_first_day_of_month(date_str):
    first_day = get_first_date_str(date_str)
    if first_day == date_str:
        return True

    return False


def get_last_week_end_date(date_str):
    last_date = str_date_delta(date_str, -CONST.TOTAL_WEEK_DAYS)
    return get_week_end_date(last_date)


def get_date_time_now_str():
    return datetime.datetime.now().strftime(CONST.DATETIME_FORMAT)


def get_date_time_now_del_str(seconds: float):
    return (datetime.datetime.now() - datetime.timedelta(seconds=seconds)).strftime(CONST.DATETIME_FORMAT)


def get_collection_name(coll_prefix, site):
    return '{}_{}'.format(coll_prefix, site)


def get_delta_time_str(seconds=0):
    delta_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    delta_time_str = delta_time.strftime(CONST.DATETIME_FORMAT)
    return delta_time_str


def get_delta_date_str(seconds=0):
    delta_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    delta_time_str = delta_time.strftime(CONST.DATE_FORMAT)
    return delta_time_str


def get_date_time_by_str(date_str):
    if not date_str:
        return None

    date_time = datetime.datetime.strptime(date_str, CONST.DATETIME_FORMAT)
    return date_time


def get_today_time_day():
    today = datetime.date.today().strftime(CONST.DATE_FORMAT)
    return today


def get_date_in_period_index(input_date):
    task_date_time = datetime.datetime.strptime(input_date, CONST.DATE_FORMAT)
    what_day_of_week = task_date_time.isoweekday()

    return what_day_of_week


def get_this_month():
    today = datetime.date.today().strftime(CONST.MONTH_DATE_FORMAT)
    month = today[0:7]

    return month


def get_last_month(input_time_str: str):
    input_time_datetime = datetime.datetime.strptime(input_time_str, CONST.MONTH_DATE_FORMAT)
    last_month_datetime = (input_time_datetime.replace(day=1) - datetime.timedelta(days=1))
    last_month_str = str(last_month_datetime)[0:7]
    return last_month_str


def get_time_range_dict(delta):
    date_time_now = datetime.datetime.now()
    delta_date_time = date_time_now + datetime.timedelta(days=delta)
    time_range = {
        CONST.SINCE: delta_date_time.strftime(CONST.DATE_FORMAT),
        CONST.UNTIL: date_time_now.strftime(CONST.DATE_FORMAT)
    }
    return time_range


def get_month_day():
    return datetime.datetime.now().strftime(CONST.MONTH_DAY_FORMAT)


def get_date_time_by_timestamp(timestamp):
    date_array = datetime.datetime.fromtimestamp(timestamp)
    date_time = date_array.strftime(CONST.DATETIME_FORMAT)
    return date_time


def get_date_by_timestamp(timestamp):
    date_array = datetime.datetime.fromtimestamp(timestamp)
    date_time = date_array.strftime(CONST.DATE_FORMAT)
    return date_time


def get_date_by_object_id(obj_id):
    timestamp = obj_id.generation_time.timestamp()
    date_time = get_date_by_timestamp(timestamp)
    return date_time


def get_time_end_str(date_str):
    return '{} {}'.format(date_str, CONST.DAY_TIME_END)


def get_time_start_str(date_str):
    return '{} {}'.format(date_str, CONST.DAY_TIME_START)


def get_datetime_zero(date_time: datetime.datetime = datetime.datetime.now()) -> datetime.datetime:
    return date_time.replace(hour=0, minute=0, second=0, microsecond=0)
