class ColorCodes:
    RESET_SEQ = '\x1b[0m'

    GREY = '\x1b[0;37;20m'
    GREEN = '\x1b[1;32m'
    YELLOW = '\x1b[33;20m'
    RED = '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    BLUE = '\x1b[1;34m'
    LIGHT_BLUE = '\x1b[1;36m'
    PURPLE = '\x1b[1;35m'
    COLORS = {
        'CRITICAL': BOLD_RED,
        'ERROR': RED,
        'WARNING': YELLOW,
        'INFO': GREEN,
        'DEBUG': BLUE,
    }
