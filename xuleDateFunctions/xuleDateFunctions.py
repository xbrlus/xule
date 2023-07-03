'''
xendrXuleFunctions

This file contains xule functions that are added to the xule processor to support xendr

Reivision number: $Change: $
'''

import calendar

def date_month_ends(xule_context, *args):
    from .xule import XuleValue as xv
    from .xule.XuleRunTime import XuleProcessingError
    try:
        raw_values = tuple(calendar.monthrange(int(args[0].value), x)[1] for x in range(1,13))
    except:
        raise XuleProcessingError(_(f"date-month-ends() functions requires a year argument, found '{args[0]}'."))
    xule_values = tuple(xv.XuleValue(xule_context, x, 'int') for x in raw_values)
    return xv.XuleValue(xule_context, xule_values, 'list')
    



