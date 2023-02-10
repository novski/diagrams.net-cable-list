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
    root = ET.parse(args.filepath).getroot()
    list_of_page_elements = root.findall("diagram")
    # start of parseing
    logger.info(f'get all cables on all pages...')
    cables_list = cables.get_cables_on_pages(list_of_page_elements)
    # start of Re-Labeling
    renumber = args.renumber
    if eval(renumber):
        renumber = False
        cables_list = cables.set_cables_on_pages(list_of_page_elements, cables_list)
    # start of export
    outputs = export.export(args, root, cables_list, list_of_page_elements)
    logger.info(f'total amount of cables: {len(cables_list)}')
    return outputs
