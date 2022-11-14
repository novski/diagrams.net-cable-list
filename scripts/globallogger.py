import os
import logging, queue
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
    level = logging.getLevelName(args.logglevel)    
    logger.setLevel(level)

    # checking if the directory for logging exist or not.
    if not os.path.exists(args.loggpath):
        os.makedirs(args.loggpath)
    
    logfile = Path(args.loggpath + args.filepath[(args.filepath.rfind('/'))+1:] +'.log')
    if os.path.exists(logfile):
        os.remove(logfile)

    log_queue     = queue.Queue()
    queue_handler = logging.handlers.QueueHandler(log_queue)       
    #set the non-blocking handler first
    logger.addHandler(queue_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # timerotating_handler = logging.handlers.TimedRotatingFileHandler(logfile, when='D', backupCount=30)
    # timerotating_handler.setLevel(level)
    # timerotating_handler.setFormatter(formatter)    
    
    # listener = logging.handlers.QueueListener(log_queue, stream_handler, timerotating_handler, respect_handler_level=True)
        
    # listener.start()

    return logger