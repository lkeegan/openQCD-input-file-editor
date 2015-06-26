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
    if remainder > 0:
        _show_consistency(field, message, False)
        return 1
    else:
        _show_consistency(field, message, True)
        return 0


def is_positive_double(field, message):
    """
    If contents of `field` is not a positive double,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    try:
        if float(field.text()) > 0:
            _show_consistency(field, message, True)
            return 0
        else:
            raise ValueError
    except ValueError:
        _show_consistency(field, message, False)
        return 1


def is_list_of_positive_doubles(field, message):
    """
    If contents of `field` is not a list of positive doubles,
    make `field` RED with tooltip caption `message` & return 1.
    Otherwise return 0.
    """
    field.setText(str(field.text()).replace(",", " "))
    for txt in str(field.text()).split():
        try:
            if float(txt) >= 0:
                _show_consistency(field, message, True)
            else:
                raise ValueError
        except ValueError:
            _show_consistency(field, message, False)
            return 1
    return 0


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
        _show_consistency(field, message, True)
    except ValueError:
        _show_consistency(field, message, False)
        return 1
    return 0

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
            if float(txt) % int(txt) == 0:
                _show_consistency(field, message, True)
            else:
                raise ValueError
    except ValueError:
        _show_consistency(field, message, False)
        return 1
    return 0


def _show_consistency(field, message, is_consistent):
    """
    If `is_consistent` is false,
    make `field` RED with tooltip caption `message`.
    Otherwise reset colour and tooltip caption of `field` to default values.
    """
    if is_consistent is True:
        field.setStyleSheet("")
        field.setToolTip("")
    else:
        field.setStyleSheet("QLineEdit { background-color : red;}")
        field.setToolTip(message)
