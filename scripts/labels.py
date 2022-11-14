import logging
from scripts import cables, helpers


logger = logging.getLogger('scraper')

def set_new_cable_label(page_elements, cable_list, new_number, page_name):
    """
    for each cable we check for the labels that are in position x:-1 (source) or x:1 (target).
    if the label is not digit or starts with 0, we relable it on both sides with the new Number.
    """
    cable_label_elements = []
    for cable in cable_list:
        flag_new_label_found = 0
        cable_id = cable.get('cable_id')
        cable_label_elements = page_elements.findall(".//*[@parent='"+str(cable_id)+"']")
        for label_element in cable_label_elements:
            label_position = get_label_position(label_element)
            if not helpers.none_or_empty(label_position):
                if label_position == 'source' or label_position == 'target':
                    label_text = helpers.get_value_here_or_in_parent(label_element,"value","label")
                    if not label_text.isdigit() and str(label_text[0:1]) != '0':
                        flag_new_label_found = 1
                        new_number_string = create_cable_label(new_number)
                        helpers.set_here_or_in_parent(label_element, new_number_string, 'value', 'label')
                        logger.debug(f'new label found on cable_id:{cable_id}, labeled with:{new_number_string} on page:{page_name}')
        if flag_new_label_found:
            new_number = new_number + 1
    return new_number

def create_cable_label(number):
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
        if not helpers.none_or_empty(label_text):
            label_id = helpers.get_value_here_or_in_parent(element,'id')
            label_dict = {'label_'+str(counter)+'_value':label_text, 
                          'label_'+str(counter)+'_id':label_id,
                          'label_'+str(counter)+'_position':label_position
                          }
            cable_labels_dict.update(label_dict)
    return cable_labels_dict   

def get_cable_label(element):
    """ get one cable label as return text """
    label_text = helpers.get_value_here_or_in_parent(element,'value', 'label')
    label_text = cable_label_value_restriction(element, label_text)
    return label_text


def get_label_position(element):
    label_position = helpers.get_value_here_or_in_child(element,'x')
    if not helpers.none_or_empty(label_position):
        if label_position == '-1':
            label_position = 'source'
        elif label_position== '1':
            label_position = 'target'
        return label_position
    else: logger.debug(f'[!] label position of id: {element.get("id")} was empty!')

def cable_label_value_restriction(element, label_value):
    """ labels have strange strings and html tags, we filter them and return all sanitized values. """
    if not helpers.none_or_empty(label_value):
        if not label_value == '%3CmxGraphModel':
            style = helpers.get_value_here_or_in_child(element,'style')
            if not helpers.if_bold(style,label_value):
                label_value = helpers.remove_html_tags(label_value).strip()
                if not helpers.detect_special_characer(label_value):
                    return label_value
                else:
                    logger.debug(f'(cable_label_id):{element.get("id")} had special characters: {label_value} and was skipped')
            else:
                logger.debug(f'(cable_label_id):{element.get("id")} had bold text: {label_value} and was skipped')
        else:
            logger.debug(f'(cable_label_id):{element.get("id")} had strange diagrams.net string %3CmxGraphModel...')
    else:
        logger.debug(f'(cable_label_id):{element.get("id")} had an empty value')
