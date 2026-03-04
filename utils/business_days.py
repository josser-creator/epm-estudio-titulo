import datetime


def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """
    Garantiza que el datetime sea timezone-aware en UTC.
    Si es naive, se asume UTC (según contrato del sistema).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)

    return dt.astimezone(datetime.timezone.utc)


def business_days_between(start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Calcula días hábiles (lunes–viernes) entre dos fechas.
    Algoritmo O(1) basado en semanas completas.
    Normaliza ambos datetimes a UTC-aware.
    """

    start = _ensure_utc(start)
    end = _ensure_utc(end)

    if start > end:
        return 0

    start_date = start.date()
    end_date = end.date()

    total_days = (end_date - start_date).days

    if total_days <= 0:
        return 0

    full_weeks = total_days // 7
    extra_days = total_days % 7

    business_days = full_weeks * 5

    for i in range(extra_days):
        day = start_date + datetime.timedelta(days=full_weeks * 7 + i)
        if day.weekday() < 5:
            business_days += 1

    return business_days