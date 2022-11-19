import os
import logging
from pathlib import Path
import logging.handlers



def setup_custom_logger(args, name):
    formatter = logging.Formatter('%(asctime)s {%(levelname)s} %(filename)s:[%(lineno)s]:%(funcName)s() %(message)s')

    logger = logging.getLogger(name)
    #clean the handlers, otherwise you get duplicated records when logging
    if (logger.hasHandlers()):
        return logger
        #logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)

    # checking if the directory for logging exist or not.
    if not os.path.exists(args.loggpath):
        os.makedirs(args.loggpath)
    
    logfile = Path(args.loggpath + args.filepath[(args.filepath.rfind('/'))+1:] +'.log')

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