import logging
from lxml import etree as ET
import csv, json
from scripts import helpers


logger = logging.getLogger('scraper')

def export(args, root, cables_list, list_of_page_elements):

    # if the argparse -o value is set use that filename as output else add output to the filename
    # in both cases use the path and save the file where it comes from.
    path_index = args.filepath.rfind('/')
    path = args.outputpath if args.outputpath else args.filepath[:path_index+1] 
    if args.outputname:
        filename = args.outputname + '-output.drawio'
    else:
        full_filename = args.filepath[path_index+1:]
        extension_index = full_filename.rfind('.')
        filename = full_filename[:extension_index] + '-output.drawio'
    output_filepath = path + filename
    output_filepaths = []
    if eval(args.renumber):
        logger.info('creating drawio...')
        output_drawio = create_drawio(output_filepath,root)
        output_filepaths.append(output_drawio)
    if args.cablesheet == 'csv':
        logger.info('creating csv...')
        output_csv = create_csv(output_filepath, cables_list)
        output_filepaths.append(output_csv)
    elif args.cablesheet == 'json':
        logger.info('creating json...')
        for page_elements in list_of_page_elements:
            page_name = page_elements.get('name')
            output_json = create_json(output_filepath, cables_list,page_name)
        output_filepaths.append(output_json)
    return output_filepaths

def create_drawio(output_filepath, root):
    output = output_filepath 
    tree = ET.ElementTree(root)
    tree.write(output, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return output

def create_csv(output_filepath,cables_list):
    output = output_filepath + '.csv'
    title = [
        'Page', 
        'Source Tag', 
        'Source Device', 
        'Source Interface',
        '-',
        'Target Interface', 
        'Target Device',
        'Target Tag'
        ]
    csv_cable_list = []
    for cable_dict in cables_list:
        page_name =  cable_dict.get("page_name")
        source_number =  cable_dict.get("label_0_value")
        source_text =  cable_dict.get("source_text")
        target_text =  cable_dict.get("target_text")
        target_number =  cable_dict.get("label_1_value")
        source_parents = cable_dict.get("source_parents")
        source_parents_texts = ''
        target_parents = cable_dict.get("target_parents")
        target_parents_texts = ''
        if not helpers.none_or_empty(source_parents):
            source_parents_texts = [x["text"] for x in  source_parents]
        if not helpers.none_or_empty(target_parents):
            target_parents_texts = [x["text"] for x in  target_parents]
        line = [page_name]
        if not source_number is None:
            line.append("'"+source_number)
        else: line.append('-')
        if not source_parents_texts is None:
            if len(source_parents_texts) > 1:
                source_parents_text = ', '.join(source_parents_texts)
                line.append(source_parents_text)
            else: line.extend(source_parents_texts)
        else: line.append('-')
        if not source_text is None:
            line.append(source_text)
        else: line.append('-')
        line.append("-")
        if not target_text is None:
            line.append(target_text)
        else: line.append('-')
        if not target_parents_texts is None:
            if len(target_parents_texts) > 1:
                target_parents_text = ', '.join(target_parents_texts)
                line.append(target_parents_text)
            else: line.extend(target_parents_texts)
        else: line.append('-')
        if not target_number is None:
            line.append("'"+target_number)
        else: line.append('-')
        csv_cable_list.append(line)
    with open(output, 'w') as csvfile:
        filewriter = csv.writer(
            csvfile, 
            delimiter=',',
            quoting=csv.QUOTE_MINIMAL
            )
        filewriter.writerow(title)
        for csv_cable in csv_cable_list:
            filewriter.writerow(csv_cable)
    return output    

def create_json(output_filepath,cables_list,page_name):
    output = output_filepath + '.json'
    with open(output, 'w') as f:
        f.write(json.dumps(cables_list, indent=2))
    return output