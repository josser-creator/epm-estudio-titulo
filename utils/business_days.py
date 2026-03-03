import datetime


def business_days_between(start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Calcula días hábiles (lunes–viernes) entre dos fechas.
    Algoritmo O(1) basado en semanas completas.
    """
    if start > end:
        return 0

    start_date = start.date()
    end_date = end.date()

    total_days = (end_date - start_date).days
    full_weeks = total_days // 7
    extra_days = total_days % 7

    business_days = full_weeks * 5

    for i in range(extra_days):
        day = start_date + datetime.timedelta(days=full_weeks * 7 + i)
        if day.weekday() < 5:  # 0=Lunes, 6=Domingo
            business_days += 1

    return business_days