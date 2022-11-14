import argparse
import logging
from scripts import globallogger
import time
from scripts.scraper import scrape 


# CLI arguments:
parser = argparse.ArgumentParser()
parser.add_argument('filepath', 
                    type=str, 
                    help='add filepath')
parser.add_argument('-o', 
                    dest='outputpath', 
                    type=str, 
                    help="define where to save the generated files.")
parser.add_argument('-n', 
                    dest='outputname', 
                    type=str, 
                    help='output filename')
parser.add_argument('-c', 
                    dest='cablesheet', 
                    type=str, 
                    help="define if cablesheet should be saved. \
                         There are two choices: 'json' or 'csv'. \
                         Default is csv.", 
                    nargs='?', 
                    const='csv', 
                    default='False')
parser.add_argument('-nr', 
                    dest='renumber', 
                    type=str, 
                    help="define if the cable numbers should be . \
                         renumbered as True or False. Default is True",
                    nargs='?', 
                    const='False', 
                    default='False')
parser.add_argument('-log', 
                    dest='logglevel', 
                    type=str, 
                    help='define the logglevel. Default is INFO', 
                    nargs='?', 
                    const='INFO', 
                    default='INFO')
parser.add_argument('-loggpath', 
                    dest='loggpath', 
                    type=str, 
                    help="define if the path where the log should \
                         be stored. Default is ./log/",
                    nargs='?', 
                    const='./', 
                    default='./log/')
args = parser.parse_args()

def main(args):
     # CAUTION: only the main file should create this custom loger. 
     # The others should retrieve it. logging.getLogger('app')
     logger = globallogger.setup_custom_logger(args, 'scraper')
     print('start')
     logger.info(f'starting..')
     outputs = scrape(args)
     return outputs

if __name__ == '__main__':
    t = time.perf_counter()
    logger = logging.getLogger('scraper')
    outputs = main(args)
    logger.info(f'created files: {outputs} in {time.perf_counter()-t}sec.')