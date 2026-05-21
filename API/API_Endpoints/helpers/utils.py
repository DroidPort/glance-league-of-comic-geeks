from datetime import date
from dateutil.relativedelta import relativedelta, WE

def get_pull_list_date() -> str:
    """
    Calculate the date that should be used when retrieving a user's pull list.

    Pull lists are updated each Wednesday for League of Comic Geeks. We need to
    calculate the start date of the current pull list in order to retrieve the
    correct issues.
    """
    now = date.today()
    res = now - relativedelta(weekday=WE)

    return res.isoformat()