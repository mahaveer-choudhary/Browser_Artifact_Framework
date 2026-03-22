import datetime

def webkit_to_datetime(webkit_timestamp):
    """
    Convert Webkit timestamp (microsecond intervals since 1601-01-01) 
    to a readable datetime string (UTC).
    """
    if not webkit_timestamp:
        return ""
    
    epoch_start = datetime.datetime(1601, 1, 1)
    try:
        delta = datetime.timedelta(microseconds=int(webkit_timestamp))
        return (epoch_start + delta).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ""

def unix_to_datetime(unix_timestamp):
    """
    Convert Unix timestamp (seconds since 1970-01-01) 
    to a readable datetime string (UTC).
    """
    if not unix_timestamp:
        return ""
    
    try:
        return datetime.datetime.utcfromtimestamp(int(unix_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return ""
