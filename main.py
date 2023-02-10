import os
import time
import argparse
from scripts.globallogger import setup_custom_logger
from scripts.scraper import scrape


def main(*args):
    if args:
        args = args[0]
        logger = setup_custom_logger(args, "scraper")
    else:
        # CLI arguments:
        parser = argparse.ArgumentParser()
        parser.add_argument("filepath",
            default="." + os.sep + "tests" + os.sep + "drawings"\
                    + os.sep + "example.drawio",
            type=str,
            help="add filepath",
        )
        parser.add_argument("-o", dest="outputpath",
            type=str,
            nargs="?",
            help="define where to save the generated files.",
        )
        parser.add_argument("-n", dest="outputname", 
            type=str,
            nargs="?",
            help="output filename")
        parser.add_argument("-c", dest="cablesheet",
            type=str,
            help="define if cablesheet should be saved. \
                  There are two choices: 'json' or 'csv'.",
            nargs="?",
            const="csv",
            default="False",
        )
        parser.add_argument("-nr", dest="renumber",
            type=str,
            help="define if the cable numbers should be \
                  renumbered as True or False. Default is True",
            nargs="?",
            const="False",
            default="False",
        )
        parser.add_argument("-log", dest="logglevel",
            type=str,
            help="define the logglevel. Default is INFO",
            nargs="?",
            const="INFO",
            default="INFO",
        )
        parser.add_argument("-loggpath", dest="loggpath",
            type=str,
            help="define if the path where the log should \
                  be stored. Default is ./log/",
            nargs="?",
            const="./",
            default="./log/",
        )
        args = parser.parse_args()
        logger = setup_custom_logger(args, "scraper")
    logger.info(f"starting..\n \
                source:{args.filepath},\n \
                cablesheettype:{args.cablesheet},\n \
                renumbering: {args.renumber}"
    )
    t = time.perf_counter()
    outputs = scrape(args)
    if not outputs:
        outputs = 'no files writen, checks done'

    logger.info(
        f'created files: {outputs} in {"{:.3f}".format(time.perf_counter()-t)}sec.'
    )
    return outputs


if __name__ == "__main__":
    main()
