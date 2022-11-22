
from lxml import etree as ET
import html
import re
import json
import logging


logger = logging.getLogger('scraper')

def search_in_elements_for_group_id(elements,id):
    """ 
    searches for given parent_id in start_element and climbs up until 
    it finds the group style value. Then returns the id of the group and its parent. 
    """
    element = elements.find(".//*[@id='"+id+"']")
    if not none_or_empty(element):
        parent_id = get_value_here_or_in_child(element,'parent')
        style = get_value_here_or_in_child(element,'style')
        if not 'group' in style:
            group_id = get_value_here_or_in_child(element,'id')
        elif 'group' in style:
            group_id = id
        return group_id, parent_id

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
    match = match.group()[-2] if match else -1
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

def debugXmlFile(elements):
    """ Debug helper. Write elements to file 'output.xml'. """
    tree = ET.ElementTree(elements)
    ET.indent(tree, space="  ", level=0)
    with open('./log/outputToXmlFile.xml', 'ab') as f:
        tree.write(f, encoding='utf-8')

def debugJsonFile(input):
    with open('./log/debugJsonFile.json', 'w') as f:
        f.write(json.dumps(input, indent=2))
