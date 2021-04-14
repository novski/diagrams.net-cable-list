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
    root = ET.parse('test2.xml').getroot()
    list_of_page_elements = xpath(root,"diagram")
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

def xpath(root,selector):
    #logging.debug(f'selector:{selector}')
    return root.findall(selector)
    
def toOutputXmlFile(elements):
    """
    Debug helper. Write elements to file 'output.xml'.
    """
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
    list_of_cables_incomplete = xpath(page_elements, ".//*[@source][@target]")
    for mxCell in list_of_cables_incomplete:
        mxCell_id = get_value_here_or_in_parent(mxCell,'id')
        list_of_cables = xpath(page_elements,'.//*[@id="'+mxCell_id+'"]')
        for cable in list_of_cables:
            toOutputXmlFile(cable)
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
            
            target_dict = connection_text(page_elements, cable_target_id,'target')
            cable_dict.update(cable_dict)
            cable_dict.update(cable_label_dict)
            cable_dict.update(source_dict)            
            cable_dict.update(target_dict)
            cable_list.append(cable_dict)
    logging.debug('device_list:')
    for device in device_list:
        logging.debug(f'[cables](device_list){device}')
    return cable_list

def get_value_here_or_in_parent(element,tag):
    value = element.get(tag)
    
    if value is None:
        value = element.getparent()
        value = value.get(tag)
    return value

def get_value_here_or_in_child(element,tag):
    value = element.get(tag)
    if value is None:
        value = element.find('.*[@'+tag+']')
        value = value.attrib[tag]
    return value

def cable_label(start_element, cable_id):
    """ 
    Text elements are linked by a tag 'parent' to cables.
    Here we search for attribute 'parent' to get id and value of it.
    """
    cable_path = ".//*[@parent='"+str(cable_id)+"']"
    label_elements = xpath(start_element,cable_path)
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

def connection_text(start_element, connection_id, prefix):
    """ search for attribute 'id' to get value and parent id from it """
    connection_path = ".//*[@id='"+str(connection_id)+"']"
    text_elements = xpath(start_element,connection_path)
    texts_dict = {}
    for text_element in text_elements:
        text_id_dict = {'connection_id':connection_id}
        texts_dict.update(text_id_dict)
        text_parent_id = get_value_here_or_in_child(text_element,'parent')
        text_value = text_element.get('value')
        text_object_label = text_element.get('label')
        text_style = text_element.get('style')
        text_bold_dict = {'text_bold':False}
        text_value_dict = find_tag_position(text_value,'<b>', prefix)
        text_object_label_dict = find_tag_position(text_object_label,'<b>', prefix)
        font_style = find_style_tag_value(text_style,'fontStyle=')
        if prefix+'_text_value' in text_object_label_dict:
            if not none_or_empty(text_object_label_dict[prefix+'_text_value']):
                text_dict = text_object_label_dict
        else: text_dict = text_value_dict
        texts_dict.update(text_dict)
        if not none_or_empty(text_parent_id):
            texts_dict.update({prefix+'_text_parent_id':text_parent_id})
            parent_dict = parent_text(start_element, text_parent_id, 'parent')
            parents_list = []
            parents_dict = {}
            # TODO: have to handle groupes correctly. 
            #       Get Groupe element id and iterate over elements that have that parent_id to find bold texts. 
            # 
            # parents_dict.update(parent_dict)
            # if 'parent_id' in parent_dict:
            #     if not none_or_empty(parent_dict['parent_id']):
            #         sub_parent_dict = parent_text(start_element, parent_dict['parent_id'], 'sub-parent')
            #         parents_list.append(sub_parent_dict)
            #         if 'parent_id' in sub_parent_dict:
            #             logging.debug('    [connection_text](sub-sub-parent) does not exist. '
            #                           'Only 3 levels deep nested elements are implemented, '
            #                           'a full traceback of all parent nodes needs some more work '
            #                           f'last element: (sub-parent_id):{sub_parent_dict["parent_id"]}')
            parent_list = parents_list.append(parents_dict)
            parents_dict = {prefix+'_parents':parents_list}
            texts_dict.update(parents_dict)
        else: logging.debug('[connection_text](text_parent_id) empty')
    logging.debug(f'    [connection_text](texts_dict):{texts_dict}')
    return texts_dict

def parent_text(start_element, connection_id, prefix):
    """ search for attribute 'id' to get value and parent id from it """
    device_path = ".//*[@id='"+str(connection_id)+"']"
    parent_elements = xpath(start_element,device_path)
    parent_dict = {}
    for obj in parent_elements:
        element_id = obj.get('id')
        parent_id = obj.get('parent')
        if none_or_empty(parent_id):
            for mxCell in obj:
                parent_id = mxCell.get('parent')
        if obj.get('value') is not None:
            text = obj.get('value')
        elif obj.get('label') is not None:
            text = obj.get('label')
        else: text = ''
        text_dict = find_tag_position(text,'<b>',prefix)
        style = obj.get('style')
        if none_or_empty(style):
            for mxCell in obj:
                style = mxCell.get('style')
        text_bold_dict = {'text_bold':False}
        font_style = find_style_tag_value(style,'fontStyle=')
        if font_style == '1':
            text_bold_dict = {'text_bold':True}
        elif 'text_bold' in text_dict:
            if text_dict['text_bold'] :
                text_bold_dict = {'text_bold':True}
        parent_dict = {'id':element_id}
        if not none_or_empty(parent_id):
            parent_id_dict = {'parent_id':parent_id}
            parent_dict.update(parent_id_dict)
        parent_dict.update(text_dict)
        parent_dict.update(text_bold_dict)
    return parent_dict

def remove_html_tags(text):
    """
    Remove html tags from a string by regex. Filter all charref characters 
    with package html. Both with python3.4+ built in tools.
    """
    clean = re.compile('<.*?>')
    return html.unescape(re.sub(clean,' ', text))

def find_tag_position(text, tag, prefix):
    """
    Search for tags in a string, return position of occurence.
    """
    d = {}
    if not none_or_empty(text):
        text_value = text.find(tag)
        if text_value == -1: 
            text_bold = {'text_bold':False}
        else: 
            text_bold = {'text_bold':True}
        text = remove_html_tags(text).strip()
        d = {prefix+'_text_value':text}
        d.update(text_bold)
    return d

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

def none_or_empty(value):
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