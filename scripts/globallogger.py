import os
from datetime import datetime
import logging
from pathlib import Path
import logging.handlers



def setup_custom_logger(args, name):
    formatter = logging.Formatter('%(asctime)s {%(levelname)s} %(filename)s:[%(lineno)s]:%(funcName)s() %(message)s')

    logger = logging.getLogger(name)
    if (logger.hasHandlers()):
        return logger
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    # checking if the directory for logging exist or not.
    if not os.path.exists(args.loggpath):
        os.makedirs(args.loggpath)
    else:
        # TODO: check amount of Logs and delete if many files
        pass

    dt = datetime.now()
    dtms = f"{dt.strftime('%y%m%d_%H%M%S')}{str(dt.microsecond/1000)[:-4]}"
    logfile = str(Path(args.loggpath)) + os.path.sep + dtms +'-'+ str(Path(args.filepath).stem) +'.log'
    print(f'globallogger logfilepath:{logfile}')

    if os.path.exists(logfile):
        os.remove(logfile)

    filehandler = logging.FileHandler(logfile)
    filehandler.setLevel(logging.DEBUG)
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(logging.getLevelName(args.logglevel.upper()))

    filehandler.setFormatter(formatter)
    consolehandler.setFormatter(formatter)

    logger.addHandler(filehandler)
    logger.addHandler(consolehandler)

    return logger