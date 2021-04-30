import logging
import sys
from lxml import etree as ET
import html
import re
import time
import json


loglevel = logging.INFO

json_output = True

def scrape():
    """
    Every page in diagrams.net has its own <root> element. 
    We iterate over pages.
    Non Python default package "lxml" is needed because of the missing `.get_parent()` function
    in the default Python xml package.
    """
    logging.info('starting XML parse...')
    root = ET.parse('210428-LUMA-detail_schematics.xml').getroot()
    set_cable_label_now = True
    list_of_page_elements = root.findall("diagram")
    last_number = []
    print(f'get all cables on all pages...')
    list_of_cable_elements, cables_list = get_cables_on_pages(list_of_page_elements)
    last_number_on_page = get_last_number(cables_list)
    last_number.append(last_number_on_page)
    last_number.sort(reverse=True)
    last_number_result = last_number[0]
    if set_cable_label_now:
        set_cable_label_now = False
        print(f'set all cable labels on all pages starting at:{last_number_result}')
        list_of_cable_elements, cables_list = set_cables_on_pages(list_of_page_elements, cables_list, last_number_result)
    tree = ET.ElementTree(root)
    tree.write('output.drawio', pretty_print=True, xml_declaration=True, encoding="utf-8")
    # TODO Replace: logging.info(f'total amount of cables: {number_of_cables}')
    logging.info('Finished')

def create_json(cables_list,page_name):
    pages = {}
    pages[page_name] = cables_list
    with open('cables.json', 'a') as f:
        f.write(json.dumps(pages, indent=2))

def create_csv(cables_list):
    csv_export_dict = {}
    for cable_dict in cables_list:
        for key in cable_dict:
            if key.find('_parents') != -1:
                for d in cable_dict:
                    pass#print(f'found _parents in cable_id: {cable_dict.get("cable_id")} d:{d}')

def deleteContent(fName):
    with open('cables.json', "w"):
        pass

def get_cables_on_pages(list_of_page_elements):
    number_of_cables = 0
    deleteContent('cables.json')
    deleteContent('cables.log')
    for page_elements in list_of_page_elements:
        page_name = page_elements.get('name')
        list_of_cable_elements = get_cable_elements(page_elements)
        cables_list = get_cable_list(page_elements, list_of_cable_elements, page_name)
        if not cables_list:
            logging.info(f'There are no cables on page {page_name}')
            continue
        logging.info(f'page_name: {page_name}')
        for cable_dict in cables_list: 
            logging.info(f'(cable_dict):{cable_dict}')
        number_of_cables += len(cables_list)
        logging.info(f'amount of cables: {len(cables_list)}')
        if json_output:
            create_json(cables_list,page_name)
    return list_of_cable_elements, cables_list

def set_cables_on_pages(list_of_page_elements, cables_list, last_number):
    number_of_cables = 0
    new_number = last_number + 1
    for page_elements in list_of_page_elements:
        page_name = page_elements.get('name')
        list_of_cable_elements = get_cable_elements(page_elements)
        cables_list = get_cable_list(page_elements, list_of_cable_elements, page_name)
        if not cables_list:
            logging.info(f'There are no cables on page {page_name}')
            continue
        new_number = set_new_cable_label(page_elements, cables_list, new_number)
        cables_list = get_cable_list(page_elements, list_of_cable_elements, page_name)
        if not cables_list:
            logging.info(f'There are no cables on page {page_name}')
            continue
        logging.info(f'page_name: {page_name}')
        for cable_dict in cables_list: 
            logging.info(f'(cable_dict):{cable_dict}')
        number_of_cables += len(cables_list)
        logging.info(f'amount of cables: {len(cables_list)}')
    return list_of_cable_elements, cables_list

def get_cable_elements(page_elements):
    """
    Search for all source and target tags. 
    This leads to incomplete elements where the id is cut off. To reach the id of 
    the seldom <object> elements we have to get the parent of <mxCell>.
    """
    list_of_cable_elements = []
    list_of_cables_incomplete = page_elements.findall( ".//*[@source][@target]")
    for mxCell in list_of_cables_incomplete:
        mxCell_id = get_value_here_or_in_parent(mxCell,'id')
        if not none_or_empty(mxCell_id):
            list_of_cable_elements += page_elements.findall('.//*[@id="'+mxCell_id+'"]')
    return list_of_cable_elements

def get_cable_list(page_elements, list_of_cable_elements, page_name):
    """ 
    iterate through the 'list_of_cable_elements' and search for cable_labels and connected_text elements.
    Return a list of cable information to build exports.
    """
    cable_list = []
    device_list = []
    if not list_of_cable_elements:
        return None
    for cable in list_of_cable_elements:
        cable_id = get_value_here_or_in_parent(cable,'id')
        cable_source_id = get_value_here_or_in_child(cable,'source')
        cable_target_id = get_value_here_or_in_child(cable,'target')
        cable_parent_id = get_value_here_or_in_child(cable,'parent')
        if cable_source_id == cable_target_id:
            logging.debug(f'(target_id) == (source_id): skipping inter box connections for design flexibility')
            continue
        cable_dict = {}
        cable_label_dict = get_cable_labels(page_elements, cable_id)
        if not none_or_empty(cable_label_dict):
            cable_dict.update(cable_label_dict)
        else: logging.debug(f'cable_label_dict of cable_id:{cable_id} was empty')
        source_dict = get_connection_text(page_elements, cable_source_id,'source')
        if not none_or_empty(source_dict):
            cable_dict.update(source_dict)
        else: logging.debug(f'source_dict of cable_id:{cable_id} was empty')
        target_dict = get_connection_text(page_elements, cable_target_id,'target')
        if not none_or_empty(target_dict):
            cable_dict.update(target_dict)
        else: logging.debug(f'target_dict of cable_id:{cable_id} was empty')
        if len(cable_dict):
            cable_dict.update({ 'page_name':page_name,
                                'cable_id':cable_id,
                                'cable_source_id':cable_source_id,  
                                'cable_target_id':cable_target_id,   
                                'cable_parent_id':cable_parent_id
                                })
            cable_list.append(cable_dict)
    logging.debug('device_list: !!!TODO!!!')
    for device in device_list:
        logging.debug(f'(device_list){device}')
    return cable_list

def set_new_cable_label(page_elements, cable_list, new_number):
    """
    for each cable we check for the labels that are in position x:-1 (source) or x:1 (target).
    if the label is not already the size of 
    """
    cable_label_elements = []
    for cable in cable_list:
        flag_new_label_found = 0
        cable_id = cable.get('cable_id')
        cable_label_elements = page_elements.findall(".//*[@parent='"+str(cable_id)+"']")
        for label_element in cable_label_elements:
            label_position = get_label_position(label_element)
            if not none_or_empty(label_position):
                if label_position == 'source' or label_position == 'target':
                    label_text = get_value_here_or_in_parent(label_element,"value","label")
                    if not label_text.isdigit() and str(label_text[0:1]) != '0':
                        flag_new_label_found = 1
                        new_number_string = calculate_cable_number(new_number)
                        set_here_or_in_parent(label_element, new_number_string, 'value', 'label')
                        print(f'new label found on cable_id:{cable_id}, labeled with:{new_number_string}')
        if flag_new_label_found:
            new_number = new_number + 1
    return new_number

def calculate_cable_number(number):
    """ fixed to my default range of cables: 00001-09999 """
    number_string = str(number)
    total_length = 5
    pading_zeros = total_length - len(number_string)
    return number_string.rjust(pading_zeros + len(number_string), '0')
     
def get_cable_labels(elements, cable_id):
    """ 
    labels have same parent_id as cable_id. Search for all attributes 'parent' 
    and grab all labels from their 'value' attribute.
    """
    label_elements = elements.findall(".//*[@parent='"+str(cable_id)+"']")
    cable_labels_dict = {}
    for counter, element in enumerate(label_elements):           
        label_text = get_cable_label(element)
        label_position = get_label_position(element)
        if not none_or_empty(label_text):
            label_id = get_value_here_or_in_parent(element,'id')
            label_dict = {'label_'+str(counter)+'_value':label_text, 
                          'label_'+str(counter)+'_id':label_id,
                          'label_'+str(counter)+'_position':label_position
                          }
            cable_labels_dict.update(label_dict)
    return cable_labels_dict   

def get_cable_label(element):
    """ get one cable label as return text """
    label_text = get_value_here_or_in_parent(element,'value', 'label')
    label_text = cable_label_value_restriction(element, label_text)
    return label_text

def get_label_position(element):
    label_position = get_value_here_or_in_child(element,'x')
    if not none_or_empty(label_position):
        if label_position == '-1':
            label_position = 'source'
        elif label_position== '1':
            label_position = 'target'
        return label_position
    else: logging.debug(f'[!] label position of id: {element.get("id")} was empty!')

def cable_label_value_restriction(element, label_value):
    """ labels have strange strings and html tags, we filter them and return all sanitized values. """
    if not none_or_empty(label_value):
        if not label_value == '%3CmxGraphModel':
            style = get_value_here_or_in_child(element,'style')
            if not if_bold(style,label_value):
                label_value = remove_html_tags(label_value).strip()
                if not detect_special_characer(label_value):
                    return label_value
                else:
                    logging.debug(f'(cable_label_id):{element.get("id")} had special characters: {label_value} and was skipped')
            else:
                logging.debug(f'(cable_label_id):{element.get("id")} had bold text: {label_value} and was skipped')
        else:
            logging.debug(f'(cable_label_id):{element.get("id")} had strange diagrams.net string %3CmxGraphModel...')
    else:
        logging.debug(f'(cable_label_id):{element.get("id")} had an empty value')

def get_last_number(cables_list):
    label_numbers = [0]
    for cable in cables_list:
        label_list = list(filter(re.compile('label_\d_value').match, cable.keys()))
        for label in label_list:
            label_text = cable.get(label)
            if not none_or_empty(label_text):
                if label_text.isdigit():
                    label_number = int(label_text)
                    label_numbers.append(label_number)
    label_numbers = list(dict.fromkeys(label_numbers))
    label_numbers.sort(reverse=True)
    return label_numbers[0]

def get_connection_text(elements, connection_id, prefix):
    """ 
    Text elements are linked by a tag 'parent' to cables.
    Search for attribute 'parent' to get id and value of it.
    """
    text_element = elements.find(".//*[@id='"+connection_id+"']")
    parents_text_list = []
    group_ids =[]
    text_dict = {}
    text_dict.update(get_text(text_element))
    if not text_dict: return
    elif none_or_empty(text_dict.get('text')): return
    elif text_dict.get('text_bold'): return
    elif text_dict.get('text') == 'both empty': return
    text_dict = rename_keys(text_dict,{'text':prefix+'_text'})
    parent_id = text_dict.get('parent_id')
    # get parent element with bold text
    parent_element = get_text(elements.find(".//*[@id='"+parent_id+"']"))
    if parent_element.get('text_bold'):
        parents_text_list.append(parent_element)
    # get grouped bold texts 
    while parent_id > '1':
        group_id, parent_id = search_in_parents_for_group_id(elements,parent_id)
        group_ids.extend([group_id])
    if not none_or_empty(group_ids):
        for num,group_id in enumerate(group_ids):
            text_dict.update({'group_id_'+str(num):group_id})
            list_of_parent_elements_in_same_group = elements.findall(".//*[@parent='"+group_id+"']")
            group_dict = search_text_in_elements(elements,list_of_parent_elements_in_same_group)
            parents_text_list.extend(group_dict)
    # get containered bold texts
    parents_container_text_dict = search_in_parents_for_container(elements,text_dict.get('parent_id'))
    if not none_or_empty(parents_container_text_dict):
        parents_text_list.append(parents_container_text_dict)
    text_dict.update({prefix+'_parents':parents_text_list})
    logging.debug(f'(texts_dict):{text_dict}')
    return text_dict

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
    get text from list of elements and append it as dict to list if it is bold. 
    """
    text_list_of_dicts = []
    for element in list_of_parent_elements_in_same_group:
        text_dict = get_text(element)
        if not none_or_empty(text_dict):
            if not none_or_empty(text_dict.get('text')):
                if text_dict.get('text_bold'):
                    text_list_of_dicts.append(text_dict)
        text_id = text_dict.get('text_id')
        text_dict = get_connected_bold_text(elements, text_id)
        if not none_or_empty(text_dict):
            if not none_or_empty(text_dict.get('text')):
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
        if text_element is None:
            return None
        text_dict = get_text(text_element)
        if not none_or_empty(text_dict.get('text')):
            if text_dict.get('text_bold'):
                return text_dict
    return None

def get_text(element):
    """ get all relevant information from a text element as dict. """
    text_dict = {}
    text_id = get_value_here_or_in_parent(element,'id')
    text_parent_id = get_value_here_or_in_child(element,'parent')
    text = a_or_b_if_populated(element.get('value'), element.get('label'))
    style = get_value_here_or_in_child(element,'style')
    bold_text_occurrance = if_bold(style,text)
    if bold_text_occurrance is True:
        text_bold_dict = {'text_bold':True}
    else: text_bold_dict = {'text_bold':False}
    style = get_value_here_or_in_child(element,'style')
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

def if_bold(style,text):
    bold_text_occurrance = find_tag_position(text,'<b>')
    if not none_or_empty(bold_text_occurrance):
        if bold_text_occurrance == -1: 
            bold_text_occurrance = False
        else: 
            bold_text_occurrance = True
    font_style = find_style_tag_value(style,'fontStyle=')
    if font_style == '1' or bold_text_occurrance is True:
        return True
    else: False

def find_tag_position(text, tag):
    """
    Search for tags in a string, return position of occurrance.
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

def get_value_here_or_in_parent(element,here_tag, parent_tag='no'):
    """ get(tag), if 'None' get parent element and return value. """
    value = element.get(here_tag)
    if value is None:
        parent = element.getparent()
        if parent is None:
            return None
        value = parent.get(here_tag)
        if value is None:
            value = parent.get(parent_tag)
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

def set_here_or_in_parent(element, value, here_tag, parent_tag='no'):
    """ 
    get(tag), if 'None' get parent element and set to new value. 
    in any case check the set value and return it value. 
    """
    here_value = element.get(here_tag)
    if here_value is None:
        parent = element.getparent()
        if parent is None:
            value = None
            logging.debug(f'[!] whether here nor parent tag was present!')
        else:
            parent.set(parent_tag,value)
            value = parent.get(parent_tag)
    else: 
        element.set(here_tag,value)
        value = element.get(here_tag)
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

def toOutputXmlFile(elements):
    """ Debug helper. Write elements to file 'output.xml'. """
    tree = ET.ElementTree(elements)
    ET.indent(tree, space="  ", level=0)
    with open('output.xml', 'ab') as f:
        tree.write(f, encoding='utf-8')


if __name__ == '__main__':
    logging.basicConfig(
        filename='cables.log',
        level=loglevel,
        format='%(asctime)s '
        '%(filename)s:%(lineno)s '
        '[%(funcName)s()]'
        '%(message)s',
        #stream=sys.stdout   
        )
    scrape()