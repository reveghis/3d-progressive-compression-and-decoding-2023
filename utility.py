def limit_value(value,min,max):
    if value > max:
        value -= (max - min + 1)
    elif value < min:
        value += (max - min + 1)
    return value