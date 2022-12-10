def validate_int(string):
    if string == None:
        return None
    if len(string):
        return int(string)
    return None
