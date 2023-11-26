import datetime
from datetime import time
import calendar


def is_last_day_of_month(year, month, day):
    last_day = calendar.monthrange(year, month)[1]
    return day == last_day


def get_24_hours_tf(anchor=None):
    if anchor == None:
        today = datetime.datetime.now().date()
    else:
        today = anchor
    start_time = datetime.datetime.combine(today, time.min).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = datetime.datetime.combine(today, time.max).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return start_time, end_time


def get_24_hours_tf_from_limit(time_limit, anchor=None):
    if anchor == None:
        current_date = datetime.datetime.now().date()
    else:
        current_date = anchor
    try:
        time_limit = datetime.datetime.strptime(time_limit, '%I:%M:%S %p').time()
    except:
        return False, False

    start_datetime = datetime.datetime.combine(current_date, time_limit) - datetime.timedelta(hours=24)
    end_datetime = datetime.datetime.combine(current_date, time_limit)

    start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return start_time, end_time


def get_72_hours_tf_from_limit(time_limit):
    current_date = datetime.datetime.now().date()
    time_limit = datetime.datetime.strptime(time_limit, '%I:%M:%S %p').time()

    start_datetime = datetime.datetime.combine(current_date, time_limit) - datetime.timedelta(hours=72)
    end_datetime = datetime.datetime.combine(current_date, time_limit)

    start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return start_time, end_time


def get_7_days_tf_from_limit(item, current_date):
    time_limit = datetime.datetime.strptime(item['end_time'], '%I:%M:%S %p').time()
    start_datetime = datetime.datetime.combine(current_date, time_limit) - datetime.timedelta(days=7)
    end_datetime = datetime.datetime.combine(current_date, time_limit)
    start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    return start_time, end_time


def get_limit_between_dates(start_date, end_date):
    weekdays = []
    current_date = start_date
    while current_date < end_date:
        if current_date.weekday() == 5 or current_date.weekday() == 6:  # Monday or Friday
            weekdays.append(current_date)
        current_date += datetime.timedelta(days=1)
    return weekdays


def get_month_weekdays(start_date, end_date):
    current_date = start_date
    subframes = []
    current_subframe = []

    while current_date <= end_date:
        if current_date == end_date:
            pass
        if current_date.weekday() < 5:  # Monday to Friday (0 to 4)
            current_subframe.append(current_date)
        else:
            if current_subframe:
                subframes.append(current_subframe)
                current_subframe = []

        current_date += datetime.timedelta(days=1)
    if current_subframe != []:
        subframes.append(current_subframe)
    return subframes


def get_7_weekdays_tf_from_limit_no_we(item, current_date):
    time_limit = datetime.datetime.strptime(item['end_time'], '%I:%M:%S %p').time()
    start_datetime = datetime.datetime.combine(current_date, time_limit) - datetime.timedelta(days=7)
    end_datetime = datetime.datetime.combine(current_date, time_limit)
    start_time = start_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    end_time = end_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    start_datetime = datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    end_datetime = datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    left_limit, right_limit = get_limit_between_dates(start_datetime, end_datetime)
    return left_limit.replace(hour=0).strftime('%Y-%m-%dT%H:%M:%S.%fZ'), right_limit.replace(hour=23, minute=59,
                                                                                             second=59).strftime(
        '%Y-%m-%dT%H:%M:%S.%fZ')

