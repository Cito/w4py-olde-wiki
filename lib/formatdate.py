"""
Does time-sensitive formatting of dates.
"""
import datetime

def format_date(date, nonbreaking=False):
    """
    Format a date relative to the current time (i.e., greater
    precision if the date is recent).  Returns a string.  Accepts
    a datetime object or an integer timestamp.

    If nonbreaking=True, then spaces will be replace with &nbsp;
    """
    if isinstance(date, (int, long)):
        date = datetime.datetime.fromtimestamp(date)
    now = datetime.datetime.now()
    dist = now - date
    if now.year != date.year:
        result = date.strftime("%d %b '%y")
    elif dist.days < 1:
        result = format_hour(date)
    elif dist.days < 2:
        result = 'Yest. %s' % format_hour(date)
    elif dist.days < 7:
        result = date.strftime('%a ') + format_hour(date)
    else:
        result = date.strftime('%d %b')
    if nonbreaking:
        result = result.replace(' ', '&nbsp;')
    return result

def format_hour(date):
    hour = date.hour
    ampm = 'am'
    if hour >= 12:
        hour -= 12
        ampm = 'pm'
    if hour == 0:
        hour = 12
    return '%i:%02i%s' % (hour, date.minute, ampm)
