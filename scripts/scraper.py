import logging
from lxml import etree as ET
from scripts import cables, export


logger = logging.getLogger('scraper')

def scrape(args):
    """
    Every page in diagrams.net has its own <root> element. 
    We iterate over pages.
    Non Python default package "lxml" is needed because of the missing `.get_parent()` function
    in the default Python xml package.
    """
    logger.info(f'filepath:{args.filepath}')
    logger.info('starting XML parse...')
    root = ET.parse(args.filepath).getroot()
    list_of_page_elements = root.findall("diagram")
    # start of parseing
    logger.info(f'get all cables on all pages...')
    last_number = []
    list_of_cable_elements, cables_list = cables.get_cables_on_pages(list_of_page_elements)
    last_number = cables.get_last_number(cables_list)
    # start of Re-Labeling
    set_cable_label_now = eval(args.renumber)
    if set_cable_label_now:
        set_cable_label_now = False
        logger.info(f'set all cable labels on all pages starting with last number:{last_number}')
        list_of_cable_elements, cables_list = cables.set_cables_on_pages(list_of_page_elements, cables_list, last_number)
    # start of export
    outputs = export.export(args, root, cables_list, list_of_cable_elements, list_of_page_elements)
    # TODO Replace: logger.info(f'total amount of cables: {number_of_cables}')
    return outputs
