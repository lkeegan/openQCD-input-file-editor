"""
Input file editor for openQCD
https://github.com/lkeegan/openQCD-input-file-editor
http://luscher.web.cern.ch/luscher/openQCD

Consistency checks module
"""


def is_integer_multiple(field, unitfield, message):
    """
    If contents of `field` is not integer multiple of contents of `unitfield`,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    remainder = int(field.text()) % int(unitfield.text())
    is_consistent = (remainder == 0)
    return _show_consistency(field, message, is_consistent)


def is_positive_double(field, message):
    """
    If contents of `field` is not a positive double,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    try:
        is_consistent = (float(field.text()) > 0)
    except ValueError:
        is_consistent = False
    return _show_consistency(field, message, is_consistent)


def is_list_of_positive_doubles(field, message):
    """
    If contents of `field` is not a list of positive doubles,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    field.setText(str(field.text()).replace(",", " "))
    for txt in str(field.text()).split():
        try:
            if not (float(txt) >= 0):
                raise ValueError
        except ValueError:
            return _show_consistency(field, message, False)
    return _show_consistency(field, message, True)


def is_list_of_n_doubles(field, num, message):
    """
    If contents of `field` is not a list of n doubles,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    field.setText(str(field.text()).replace(",", " "))
    try:
        if len(str(field.text()).split()) != num:
            raise ValueError
        for txt in str(field.text()).split():
            float(txt)
    except ValueError:
        return _show_consistency(field, message, False)
    return _show_consistency(field, message, True)


def is_list_of_n_positive_integers(field, num, message):
    """
    If contents of `field` is not a list of `num` positive integers,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    field.setText(str(field.text()).replace(",", " "))
    try:
        if len(str(field.text()).split()) != num:
            raise ValueError
        for txt in str(field.text()).split():
            if not (float(txt) % int(txt) == 0):
                raise ValueError
    except ValueError:
        return _show_consistency(field, message, False)
    except ZeroDivisionError:
        return _show_consistency(field, message, False)
    return _show_consistency(field, message, True)


def _show_consistency(field, message, is_consistent):
    """
    If `is_consistent` is false,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise reset colour and tooltip caption of `field` to
    default values, and return 0.
    """
    if is_consistent is True:
        field.setStyleSheet("")
        field.setToolTip("")
        return 0
    else:
        field.setStyleSheet("QLineEdit { background-color : red;}")
        field.setToolTip(message)
        return 1
