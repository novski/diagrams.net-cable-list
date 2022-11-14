import html
import re
import logging
from scripts import labels, helpers, cables


logger = logging.getLogger('scraper')

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
        text_dict = cables.get_text(element)
        if not none_or_empty(text_dict):
            if not none_or_empty(text_dict.get('text')):
                if text_dict.get('text_bold'):
                    text_list_of_dicts.append(text_dict)
        text_id = text_dict.get('text_id')
        text_dict = cables.get_connected_bold_text(elements, text_id)
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
        text_dict = cables.get_text(element)
        if text_dict.get('container') and text_dict.get('connectable'):
            text_id = text_dict.get('text_id')
            text_dict = cables.get_connected_bold_text(elements, text_id)
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

    match = re.search(f"{tag}(.+?);",text)
    match = match.groups(1) if match else -1
    return match

    

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
            logger.debug(f'[!] whether here nor parent tag was present!')
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