from lxml import etree as ET
import re
import logging
from scripts import labels, helpers


logger = logging.getLogger('scraper')

def get_cables_on_pages(list_of_page_elements):
    number_of_cables = 0
    cables_list = []
    for page_elements in list_of_page_elements:
        page_name = page_elements.get('name')
        cables_on_pages_list = get_cable_list(page_elements, page_name)
        if not cables_on_pages_list:
            logger.info(f'page_name:{page_name} - There are no cables on this page')
            continue
        for cable_dict in cables_on_pages_list: 
            logger.debug(f'page_name:{page_name} - (cable_dict):{cable_dict}')
        logger.info(f'page_name:{page_name} - amount of cables: {len(cables_on_pages_list)}')
        cables_list += cables_on_pages_list
    return cables_list

# TODO! get_cables_on_pages and set_cables_on_pages have double code snipets and get invoked to many times.
# try if a abstraction of pages to cables in total is fisible and inject the pagename somehow more consistent.

def set_cables_on_pages(list_of_page_elements, cables_list):
    """
    Here we get the cables from one page and set the new labels on it.
    Then we get the cables from the same page again and store it in the cables_list
    and return the list of cables.
    """
    last_number = get_last_number(cables_list)
    logger.info(f'set all cable labels on all pages starting with last number:{last_number}')
    new_number = last_number + 1
    cables_list = []
    for page_elements in list_of_page_elements:
        page_name = page_elements.get('name')
        cables_on_pages_list = get_cable_list(page_elements, page_name)
        if not cables_on_pages_list:
            logger.info(f'page_name:{page_name} - There are no cables on this page')
            continue
        new_number = labels.set_new_cable_label(page_elements, cables_on_pages_list, new_number, page_name)
        cables_on_pages_list = get_cable_list(page_elements, page_name)
        if not cables_on_pages_list:
            logger.info(f'page_name:{page_name} - There are still no cables on this page')
            continue
        for cable_dict in cables_on_pages_list: 
            logger.debug(f'page_name:{page_name} - (cable_dict):{cable_dict}')
        logger.info(f'page_name:{page_name} - amount of cables: {len(cables_on_pages_list)}')
        cables_list += cables_on_pages_list
    return cables_list

def get_cable_list(page_elements, page_name):
    """ 
    iterate through the 'list_of_cable_elements' and search for cable_labels 
    (on the hole page) and connected_text elements.
    Return a list of cable information to build exports.
    """
    cable_list = []
    device_list = []
    list_of_cable_elements = get_cable_elements(page_elements)
    logger.debug(f'\n{page_name} has {len(list_of_cable_elements)} cable elements')
    if not list_of_cable_elements: # in case of pages with no connections
        return None
    for cable in list_of_cable_elements:
        cable_id = helpers.get_value_here_or_in_parent(cable,'id')
        source_id = helpers.get_value_here_or_in_child(cable,'source')
        target_id = helpers.get_value_here_or_in_child(cable,'target')
        parent_id = helpers.get_value_here_or_in_child(cable,'parent')
        if source_id == target_id:
            logger.debug(f'(target_id) == (source_id): skipping inter box connections for design flexibility')
            continue
        cable_dict = {}
        cable_label_dict = labels.get_cable_labels(page_elements, cable_id)
        if not helpers.none_or_empty(cable_label_dict):
            cable_dict.update(cable_label_dict)
        else: logger.debug(f'cable_label_dict of cable_id:{cable_id} was empty')
        source_dict = get_connection_text(page_elements, source_id,'source')
        if not helpers.none_or_empty(source_dict):
            cable_dict.update(source_dict)
        else: logger.debug(f'source_dict of cable_id:{cable_id} was empty')
        target_dict = get_connection_text(page_elements, target_id,'target')
        if not helpers.none_or_empty(target_dict):
            cable_dict.update(target_dict)
        else: logger.debug(f'target_dict of cable_id:{cable_id} was empty')
        #cable_dict.update({"len(cable_dict)":len(cable_dict)})
        if len(cable_dict):
            cable_dict.update({ 'page_name':page_name,
                                'cable_id':cable_id,
                                'source_id':source_id,  
                                'target_id':target_id,   
                                'parent_id':parent_id
                                })
            cable_list.append(cable_dict)
    helpers.debugJsonFile(cable_list)
    logger.debug('device_list: !!!TODO!!!')   
    for device in device_list:
        logger.debug(f'(device_list){device}')
    return cable_list

def get_cable_elements(page_elements):
    """
    Search for all source and target tags. 
    This leads to incomplete elements where the id is cut off. To reach the id of 
    the seldom <object> elements we have to get the parent of <mxCell>.
    This (to reach the parent) is also why we need lxml and no the python standard xml library.
    """
    list_of_cable_elements = []
    list_of_cables_incomplete = page_elements.findall( ".//*[@source][@target]")
    for mxCell in list_of_cables_incomplete:
        mxCell_id = helpers.get_value_here_or_in_parent(mxCell,'id')
        if not helpers.none_or_empty(mxCell_id):
            list_of_cable_elements += page_elements.findall('.//*[@id="'+mxCell_id+'"]')
    return list_of_cable_elements

def get_last_number(cables_list):
    label_numbers = [0]
    for cable in cables_list:
        label_list = list(filter(re.compile('label_\d_value').match, cable.keys()))
        for label in label_list:
            label_text = cable.get(label)
            if not helpers.none_or_empty(label_text):
                if label_text.isdigit():
                    label_number = int(label_text)
                    label_numbers.append(label_number)
    label_numbers = list(dict.fromkeys(label_numbers))
    label_numbers.sort(reverse=True)
    return label_numbers[0]

def get_connection_text(elements, text_id, prefix):
    """ 
    Text elements connected to cables are linked by a id to the cable source of target tag.
    Search for attribute 'id=text_id' to get id and value of the Text element.
    """
    text_element = elements.find(".//*[@id='"+text_id+"']")
    parents_text_list = []
    group_ids =[]
    text_dict = {}

    text_dict.update(get_text(text_element))
    if not text_dict: return
    elif helpers.none_or_empty(text_dict.get('text')): return
    elif text_dict.get('text_bold'): return
    elif text_dict.get('text') == 'both empty': return

    text_dict = helpers.rename_keys(text_dict,{'text':prefix+'_text'})
    parent_id = text_dict.get('parent_id')
    # get parent element with bold text
    parent_element = get_text(elements.find(".//*[@id='"+parent_id+"']"))
    if parent_element.get('text_bold'):
        parents_text_list.append(parent_element)
    # get grouped bold texts 
    while parent_id > '1':
        group_id, parent_id = helpers.search_in_elements_for_group_id(elements,parent_id)
        group_ids.extend([group_id])
    if not helpers.none_or_empty(group_ids):
        for num,group_id in enumerate(group_ids):
            text_dict.update({prefix+'_group_id_'+str(num):group_id})
            list_of_parent_elements_in_same_group = elements.findall(".//*[@parent='"+group_id+"']")
            group_dict = search_text_in_elements(elements,list_of_parent_elements_in_same_group)
            parents_text_list.extend(group_dict)
    # get containered bold texts
    parents_container_text_dict = search_in_parents_for_container(elements,text_dict.get('parent_id'))
    if not helpers.none_or_empty(parents_container_text_dict):
        parents_text_list.append(parents_container_text_dict)
    text_dict.update({prefix+'_parents':parents_text_list})
    logger.debug(f'(texts_dict):{text_dict}')
    return text_dict

def get_text(element):
    """ get all relevant information from a text element as dict. """
    text_dict = {}
    text_id = helpers.get_value_here_or_in_parent(element,'id')
    text_parent_id = helpers.get_value_here_or_in_child(element,'parent')
    text = helpers.a_or_b_if_populated(element.get('value'), element.get('label'))
    style = helpers.get_value_here_or_in_child(element,'style')
    bold_text_occurrance = helpers.if_bold(style,text)
    if bold_text_occurrance is True:
        text_bold_dict = {'text_bold':True}
    else: text_bold_dict = {'text_bold':False}
    style = helpers.get_value_here_or_in_child(element,'style')
    container_style = helpers.find_style_tag_value(style,'container=')
    if not helpers.none_or_empty(container_style):
        if container_style == '1':
            container_dict = {'container':True}
        else: container_dict = {'container':False}
    else: container_dict = {'container':False}
    connectable_style = helpers.find_style_tag_value(style,'connectable=')
    if not helpers.none_or_empty(connectable_style):
        if connectable_style == '1':
            connectable_dict = {'connectable':True}
        else: connectable_dict = {'connectable':False}
    else: connectable_dict = {'connectable':False}
    text = helpers.remove_html_tags(text).strip()
    text_dict.update({'text_id':text_id})
    text_dict.update({'parent_id':text_parent_id})
    text_dict.update({'text':text})
    text_dict.update(text_bold_dict)
    text_dict.update(container_dict)
    text_dict.update(connectable_dict)
    return text_dict

def search_text_in_elements(elements,list_of_parent_elements_in_same_group):
    """ 
    get text from list of elements and append it as dict to list if it is bold. 
    """
    text_list_of_dicts = []
    for element in list_of_parent_elements_in_same_group:
        text_dict = get_text(element)
        if not helpers.none_or_empty(text_dict):
            if not helpers.none_or_empty(text_dict.get('text')):
                if text_dict.get('text_bold'):
                    text_list_of_dicts.append(text_dict)
        text_id = text_dict.get('text_id')
        text_dict = get_connected_bold_text(elements, text_id)
        if not helpers.none_or_empty(text_dict):
            if not helpers.none_or_empty(text_dict.get('text')):
                text_list_of_dicts.append(text_dict)
    return text_list_of_dicts

def search_in_parents_for_container(elements,parent_id):
    """ 
    Use parent id to look up style for container. 
    If container found search with container_id for source or target tag entry. 
    If source id maches get target id and its text or vice versa.
    """
    if not helpers.none_or_empty(parent_id):
        element = elements.find(".//*[@id='"+parent_id+"']")
        text_dict = get_text(element)
        if text_dict.get('container') and text_dict.get('connectable'):
            text_id = text_dict.get('text_id')
            text_dict = get_connected_bold_text(elements, text_id)
            return text_dict

def get_connected_bold_text(elements,text_id):
    """ 
    Find text_id in 'source' or 'target' 'tags' and get the bold text of 
    the opposite cable end and only return if it is not empty. 
    """
    cable_a = elements.find(".//*[@source='"+text_id+"']")
    cable_b = elements.find(".//*[@target='"+text_id+"']")
    if helpers.none_or_empty(cable_a) and not helpers.none_or_empty(cable_b):
        cable = cable_b
        cable_dir = helpers.get_value_here_or_in_child(cable,'source')  
    elif not helpers.none_or_empty(cable_a) and helpers.none_or_empty(cable_b):
        cable = cable_a
        cable_dir = helpers.get_value_here_or_in_child(cable,'target')
    elif helpers.none_or_empty(cable_a) and helpers.none_or_empty(cable_b):
        cable = ''
    else: cable = ''
    if not helpers.none_or_empty(cable):
        cable_id = helpers.get_value_here_or_in_parent(cable,'id')
        text_element = elements.find(".//*[@id='"+cable_dir+"']")
        if text_element is None:
            return None
        text_dict = get_text(text_element)
        if not helpers.none_or_empty(text_dict.get('text')):
            if text_dict.get('text_bold'):
                return text_dict
    return None


