import time
try:
    from mx import DateTime
except ImportError:
    DateTime = None
try:
    from datetime import datetime
except ImportError:
    datetime = None

def _days(d):
    if isinstance(d, datetime):
        return time.mktime(d.timetuple()) / 60 / 60 / 24
    elif isinstance(d, DateTime.DateTimeType):
        return d.day_of_year
    elif isinstance(d, time.struct_time):
        return time.mktime(d) / 60 / 60 / 24
    else:
        return d.dayOfYear()

def format_date_relative(date):
    """
    Formats a date relative to the current time.  The result
    will be dates like 'Yesterday', 'Wednesday 10:00am',
    '12 May 2003', etc.

    Specifically:

      * If in the last 24 hours, just give the time.
      * If yesterday, give 'yesterday TIME'
      * If in the last 7 days, give 'DAY_OF_WEEK TIME'
      * If in the same calendar year, give 'DAY_OF_MONTH MONTH'
      * Otherwise gives 'DAY_OF_MONTH MONTH YEAR'

    It uses english names when appropriate (e.g., Apr or Thu).
    """
    if date is None:
        return ''
    now = DateTime.now()
    year = date.year
    if callable(year):
        year = year()
    month = date.month
    if callable(month):
        month = month()
    day = date.day
    if callable(day):
        day = day()
    day_of_year = _days(date)
    if now.year == year:
        if now.month == month:
            if _days(now) - 7 < day_of_year:
                if now.day == day:
                    return format_time(date)
                elif now.day - 1 == day:
                    return 'Yesterday %s' % format_time(date)
                else:
                    return date.strftime('%a ') + format_time(date)
            elif _days(now) - 21 < day_of_year:
                return date.strftime('%a %d %b')
            else:
                return date.strftime('%d %b')
        else:
            return date.strftime('%d %b')
    else:
        return date.strftime('%d %b \'%y')

def format_time(date):
    """
    Formats the time, like 4:20pm; unlike strftime, it lower-cases
    the am/pm, and doesn't create hours with leading zeros.
    """
    text = date.strftime('%I:%M%p')
    text = text[:-2] + text[-2:].lower()
    if text.startswith('0'):
        text = text[1:]
    return text
