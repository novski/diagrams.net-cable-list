import logging
from lxml import etree as ET
import csv, json


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
    csv_export_dict = {}
    for cable_dict in cables_list:
        #logger.debug(f'csv-cable_dict:{cable_dict}')
        for key in cable_dict:
            if key.find('_parents') != -1:
                for d in cable_dict:
                    pass#logger.debug(f'found _parents in cable_id: {cable_dict.get("cable_id")} d:{d}')
    # with open(output, 'w') as csvfile:
    #     filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #     filewriter.writerow(['Name', 'Profession'])
    return output    

def create_json(output_filepath,cables_list,page_name):
    output = output_filepath + '.json'
    pages = {}
    pages[page_name] = cables_list
    with open(output, 'w') as f:
        f.write(json.dumps(cables_list, indent=2))
    return output