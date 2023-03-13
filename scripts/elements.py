from lxml import etree as ET
import re
import logging
from scripts import labels, helpers


logger = logging.getLogger('scraper')

def get_type_elements(page_elements):
    """
    Search for all elements with an attribute "type"
    """
    list_of_elements = []
    list_of_elements_incomplete = page_elements.findall( ".//*[@type]")
    for mxCell in list_of_elements_incomplete:
        mxCell_id = helpers.get_value_here_or_in_parent(mxCell,'id')
        if not helpers.none_or_empty(mxCell_id):
            list_of_elements += page_elements.findall('.//*[@id="'+mxCell_id+'"]')
    return list_of_elements