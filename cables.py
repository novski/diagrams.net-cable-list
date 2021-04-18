import logging
from lxml import etree as ET
import html
import re
import time


def scrape():
    """
    Every page in diagrams.net has its own <root> element. 
    We iterate over pages.
    """
    logging.info('starting XML parse...')
    root = ET.parse('test.xml').getroot()
    list_of_page_elements = root.findall("diagram")
    number_of_cables = 0
    for page_elements in list_of_page_elements:
        page_name = page_elements.get('name')
        cables_list = cables(page_elements, page_name)
        cable_list_length = len(cables_list)
        logging.info(f'page_name: {page_name}')
        for cable_dict in cables_list: 
            logging.info(f'[scrape](cable_dict):{cable_dict}')
        number_of_cables += cable_list_length
        logging.info(f'amount of cables: {cable_list_length}')
    logging.info(f'total amount of cables: {number_of_cables}')
    logging.info('Finished')
    
def toOutputXmlFile(elements):
    """ Debug helper. Write elements to file 'output.xml'. """
    tree = ET.ElementTree(elements)
    ET.indent(tree, space="  ", level=0)
    with open('output.xml', 'ab') as f:
        tree.write(f, encoding='utf-8')

def cables(page_elements, page_name):
    """
    Search for all source and target tags. 
    This leads to incomplete elements where the id is cut off. To reach the id of 
    the seldom <object> elements we have to get the parent of <mxCell>.
    """
    cable_list = []
    device_list = []
    list_of_cables_incomplete = page_elements.findall( ".//*[@source][@target]")
    for mxCell in list_of_cables_incomplete:
        mxCell_id = get_value_here_or_in_parent(mxCell,'id')
        if not none_or_empty(mxCell_id):
            list_of_cables = page_elements.findall('.//*[@id="'+mxCell_id+'"]')
            for cable in list_of_cables:
                cable_id = get_value_here_or_in_parent(cable,'id')
                cable_source_id = get_value_here_or_in_child(cable,'source')
                cable_target_id = get_value_here_or_in_child(cable,'target')
                cable_parent_id = get_value_here_or_in_child(cable,'parent')
                if cable_source_id == cable_target_id:
                    logging.debug(f'target_id == source_id: skipping inter box connections for design flexibility')
                    continue
                    cable_dict = {}
                cable_dict = {'page_name':page_name,
                            'cable_id':cable_id,
                            'cable_source_id':cable_source_id,  
                            'cable_target_id':cable_target_id,   
                            'cable_parent_id':cable_parent_id}
                cable_label_dict = cable_label(page_elements, cable_id)
                source_dict = connection_text(page_elements, cable_source_id,'source')
                #print(f'source_dict:{source_dict}')
                target_dict = connection_text(page_elements, cable_target_id,'target')
                #print(f'target_dict:{target_dict}')
                cable_dict.update(cable_dict)
                cable_dict.update(cable_label_dict)
                cable_dict.update(source_dict)            
                cable_dict.update(target_dict)
                cable_list.append(cable_dict)
    logging.debug('device_list:')
    for device in device_list:
        logging.debug(f'[cables](device_list){device}')
    return cable_list

def cable_label(start_element, cable_id):
    """ 
    Text elements are linked by a tag 'parent' to cables.
    Here we search for attribute 'parent' to get id and value of it.
    """
    cable_path = ".//*[@parent='"+str(cable_id)+"']"
    label_elements = start_element.findall(cable_path)
    cable_labels_dict = {}
    for counter, label_element in enumerate(label_elements):
        label_value = label_element.get('value')
        if not none_or_empty(label_value):
            if not label_value == '%3CmxGraphModel':
                label_value = remove_html_tags(label_value).strip()
                if not detect_special_characer(label_value):
                    label_id = label_element.get('id')
                    label_dict = {'label'+str(counter)+'_value':label_value, 'label'+str(counter)+'_id':label_id}
                    cable_labels_dict.update(label_dict)
                else:
                    logging.debug(f'cable_id: {cable_id} had special characters: {label_value} and was skipped')
            else:
                logging.debug(f'cable_label_id:{label_element.get("id")} had strange diagrams.net string %3CmxGraphModel...')
        else:
            logging.debug(f'cable_id: {cable_id} had an empty value')
    return cable_labels_dict

def connection_text(elements, connection_id, prefix):
    """ search for attribute 'id' to get value and parent id from it """
    text_elements = elements.findall(".//*[@id='"+connection_id+"']")
    texts_dict = {}
    parents_text_list = []
    group_ids =[]
    for text_element in text_elements:
        text_dict = {}
        text_dict.update(get(text_element))
        if not text_dict:
            continue
        elif text_dict.get('text_bold'):
            continue
        elif text_dict.get('text') == 'both empty':
            continue
        text_dict = rename_keys(text_dict,{'text':prefix+'_text'})
        parent_id = text_dict.get('parent_id')
        # get parent element with bold text
        parent_element = get(elements.find(".//*[@id='"+parent_id+"']"))
        if parent_element.get('text_bold'):
            parents_text_list.append(parent_element)
        # get grouped bold texts 
        while parent_id > '1':
            group_id, parent_id = search_in_parents_for_group_id(elements,parent_id)
            group_ids.extend([group_id])
        if not none_or_empty(group_ids):
            for group_id in group_ids:
                text_dict.update({'group_id':group_id})
                list_of_parent_elements_in_same_group = elements.findall(".//*[@parent='"+group_id+"']")
                group_dict = search_text_in_elements(elements,list_of_parent_elements_in_same_group)
                parents_text_list.extend(group_dict)
        # get containered bold texts
        parents_container_text_dict = search_in_parents_for_container(elements,text_dict.get('parent_id'))
        if not none_or_empty(parents_container_text_dict):
            parents_text_list.append(parents_container_text_dict)
        text_dict.update({'parents':parents_text_list})
        print(f'text_dict:{text_dict}')
            # parent_list = parents_list.append(parents_dict)
            # parents_dict = {prefix+'_parents':parents_list}
            # texts_dict.update(parents_dict)
        
    logging.debug(f'    [connection_text](texts_dict):{texts_dict}')
    return texts_dict

def search_in_parents_for_group_id(elements,parent_id):
    """ 
    searches for given parent_id in start_element and climbs up until 
    if finds the group style value. Then returns the id of the group and its parent. 
    """
    element = elements.find(".//*[@id='"+parent_id+"']")
    if not none_or_empty(element):
        parent_id = get_value_here_or_in_child(element,'parent')
        style = get_value_here_or_in_child(element,'style')
        if not find_style_tag_value(style, 'group') == -1:
            group_id = get_value_here_or_in_child(element,'id')
        else: group_id = ''
        return group_id, parent_id


def search_text_in_elements(elements,list_of_parent_elements_in_same_group):
    """ 
    get text from list of elements and append 
    it as dict to list if it is bold. 
    """
    text_list_of_dicts = []
    for element in list_of_parent_elements_in_same_group:
        text_dict = get(element)
        if text_dict.get('text_bold'):
            text_list_of_dicts.append(text_dict)
        text_id = text_dict.get('text_id')
        text_dict = get_connected_bold_text(elements, text_id)
        if not none_or_empty(text_dict):
            text_list_of_dicts.append(text_dict)
    return text_list_of_dicts

def search_in_parents_for_container(elements,parent_id):
    """ 
    Use parent id to look up style for container. 
    If container found search with container_id for source or target tag entry. 
    If source id maches get target id and its text or vice versa.
    """
    if not none_or_empty(parent_id):
        element = elements.find(".//*[@id='"+parent_id+"']")
        text_dict = get(element)
        if text_dict.get('container') and text_dict.get('connectable'):
            text_id = text_dict.get('text_id')
            text_dict = get_connected_bold_text(elements, text_id)
            return text_dict

def get_connected_bold_text(elements,text_id):
    cable_a = elements.find(".//*[@source='"+text_id+"']")
    cable_b = elements.find(".//*[@target='"+text_id+"']")
    if none_or_empty(cable_a) and not none_or_empty(cable_b):
        cable = cable_b
        cable_dir = get_value_here_or_in_child(cable,'source')  
    elif not none_or_empty(cable_a) and none_or_empty(cable_b):
        cable = cable_a
        cable_dir = get_value_here_or_in_child(cable,'target')
    elif none_or_empty(cable_a) and none_or_empty(cable_b):
        cable = ''
    else: cable = ''
    if not none_or_empty(cable):
        cable_id = get_value_here_or_in_parent(cable,'id')
        text_element = elements.find(".//*[@id='"+cable_dir+"']")
        text_dict = get(text_element)
        if not none_or_empty(text_dict.get('text')):
            if text_dict.get('text_bold'):
                return text_dict

def get(element):
    """ get all relevant information from a text element as dict. """
    text_dict = {}
    text_id = get_value_here_or_in_parent(element,'id')
    text_parent_id = get_value_here_or_in_child(element,'parent')
    text = a_or_b_if_populated(element.get('value'), element.get('label'))
    bold_text_occurrence = find_tag_position(text,'<b>')
    if not none_or_empty(bold_text_occurrence):
        if bold_text_occurrence == -1: 
            bold_text_occurrence = False
        else: 
            bold_text_occurrence = True
    style = get_value_here_or_in_child(element,'style')
    font_style = find_style_tag_value(style,'fontStyle=')
    if font_style == '1' or bold_text_occurrence is True:
        text_bold_dict = {'text_bold':True}
    else: text_bold_dict = {'text_bold':False}
    container_style = find_style_tag_value(style,'container=')
    if not none_or_empty(container_style):
        if container_style == '1':
            container_dict = {'container':True}
        else: container_dict = {'container':False}
    else: container_dict = {'container':False}
    connectable_style = find_style_tag_value(style,'connectable=')
    if not none_or_empty(connectable_style):
        if connectable_style == '1':
            connectable_dict = {'connectable':True}
        else: connectable_dict = {'connectable':False}
    else: connectable_dict = {'connectable':False}
    text = remove_html_tags(text).strip()
    text_dict.update({'text_id':text_id})
    text_dict.update({'parent_id':text_parent_id})
    text_dict.update({'text':text})
    text_dict.update(text_bold_dict)
    text_dict.update(container_dict)
    text_dict.update(connectable_dict)
    return text_dict

def a_or_b_if_populated(a, b):
    """ return the populated property or text 'both empty' or 'both populated' """
    if none_or_empty(a) and not none_or_empty(b):
        c = b
    elif not none_or_empty(a) and none_or_empty(b):
        c = a
    elif none_or_empty(a) and none_or_empty(b):
        c = ''
    else: c = ''
    return c

def remove_html_tags(text):
    """
    Remove html tags from a string by regex. Filter all charref characters 
    with package html. Both with python3.4+ built in tools.
    """
    clean = re.compile('<.*?>')
    return html.unescape(re.sub(clean,' ', text))

def find_tag_position(text, tag):
    """
    Search for tags in a string, return position of occurence.
    """
    if not none_or_empty(text):
        text_value = text.find(tag)
    else: text_value = -1
    return text_value

def find_style_tag_value(text,tag):
    """
    Search tags from in a string, return variables behind '='.
    """
    if not none_or_empty(text):
        array =text.split(';')
        for x in array:
            if x.find(tag) != -1:
                parts = x.partition('=')
                return parts[2]

def detect_special_characer(pass_string):
    """
    method to detect special characters not including whitespaces, adapted to own version
    where the \ and ] characters are escaped with \ from Regex '[@_!#$%^&*()<>?/\\|}{~:\[\]]'
    limited version: [@!#$%^*\\\}{[\]]
    """ 
    regex= re.compile('[@_!#$%^&*()<>?/\\|}{~:\[\]]') 
    if(regex.search(pass_string) == None): result = False
    else: result = True
    return result

def get_value_here_or_in_parent(element,tag):
    """ get(tag), if 'None' get parent element and return value. """
    value = element.get(tag)
    if value is None:
        value = element.getparent()
        if value is None:
            return ''
        value = value.get(tag)
    return value

def get_value_here_or_in_child(element,tag):
    """ get(tag), if 'None' elemene.find(tag) in children's of element and return the Value. """
    value = element.get(tag)
    if value is None:
        value = element.find('.*[@'+tag+']')
        if value is None:
            return ''
        value = value.get(tag)
    return value

def rename_keys(input_dict, key_to_replace_dict):
    """
    Gets a dict, and another dict specifying how to rename keys as {'old_keyname':'new_keyname'}.
    It returns a new dict, with renamed keys.
    """
    return {key_to_replace_dict.get(k, k): v for k, v in input_dict.items()}

def none_or_empty(value):
    """ test if value is None or '' and return a boolean 'True' if so. """
    if value == None or value =='': return True
    else: return False

if __name__ == '__main__':
    logging.basicConfig(
        filename='path.log',
        format='%(levelname)s:%(message)s', 
        level=logging.INFO
        #level=logging.DEBUG
        )
    scrape()