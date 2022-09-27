from re import template
from pcpi import session_loader
from loguru import logger
import sys
import jmespath

#==================================================================================================

def convert(input):
    if type(input) == list:
        return '"' + str(input) + '"'
    else:
        return str(input)

#==================================================================================================

def print_paths(template):
    for val in template:
        print(val['path'], val['type'])

#==================================================================================================

def get_parent_path(path, template):
    for val in template:
        if val['path'] == path:
            return val['parent_path']

#==================================================================================================

def validate_fields(fields, template):
    path_list = []
    for val in template:
        path_list.append(val['path'])

    for field in fields:
        if field not in path_list:
            print(field)
            return False
    return True

#==================================================================================================

def create_query_string(path, parent_type):
    path_args = path.split('.')
    for i in range(len(path_args)):
        if ' ' in path_args[i] or '-' in path_args[i]:
            path_args[i] = '"' + path_args[i] + '"'

    root = path_args[0]

    new_path = ""
    new_path += root

    temp_path_base = root
    for index in path_args[1:]: #dont need first value
        temp_path = temp_path_base + '.' + index
        if parent_type == list:
            new_path += "[*]."
        else:
            new_path += "."

        temp_path_base = temp_path
        new_path += index

    return new_path

#==================================================================================================

#BUG jmespath returns NoneType on most searches???
def get_object_keys(json_keys: list, obj: object, path: str, parent_type: str, parent_path:str) -> list:
    curr_list = []
    for key in obj.keys():
        curr_path = ''

        if path=='':
            parent_path = path
            curr_path = key
        else:
            parent_path = path
            curr_path = path + '.' + key 

        query = create_query_string(curr_path, parent_type)

        print('Query:', query)

        value = jmespath.search(query, obj)
        my_type = type(value)
        print(my_type)
        print(value)
        print()

        if type(obj[key]) == dict:
            curr_list.append({'field':key, 'type':my_type, 'parent_type':parent_type, 'path':curr_path, 'parent_path':parent_path})
            get_object_keys(json_keys, obj[key], curr_path, my_type, parent_path)
        elif type(obj[key]) == list:
            try:
                curr_list.append({'field':key, 'type':my_type, 'parent_type':parent_type, 'path':curr_path, 'parent_path':parent_path})
                get_object_keys(json_keys, obj[key][0], curr_path, my_type, parent_path)#if list is empty this might fail
            except:
                pass
        else:
            curr_list.append({'field':key, 'type':my_type, 'parent_type':parent_type, 'path':curr_path, 'parent_path':parent_path})

    json_keys.extend(curr_list)

#==================================================================================================

def get_name(path, json_keys):
    for val in json_keys:
        if val['path'] == path:
            return val['field']

#==================================================================================================

def convert_to_query(path, json_keys):
    path_args = path.split('.')
    root = path_args[0]

    new_path = ""
    new_path += root

    temp_path_base = root
    for index in path_args[1:]: #dont need first value
        temp_path = temp_path_base + '.' + index
        for key in json_keys:
            if key['path'] == temp_path:
                if key['parent_type'] == list:
                    new_path += "[*]."
                else:
                    new_path += "."

        temp_path_base = temp_path
        new_path += index

    return new_path

#==================================================================================================

def build_csv(output_file_path, paths, json_keys, json_data):
    with open(output_file_path, 'w') as outfile:
        headers = ""
        for p in paths:
            if paths.index(p) != len(paths)-1:
                headers += p + ','
            else:
                headers += p
        headers += '\n'
        outfile.write(headers)

        for blob in json_data:
            csv_base = ''
            values = []
            list_values = []
            for path in paths:
                query = convert_to_query(path, json_keys)
                value = jmespath.search(query, blob)
                if type(value) != list:
                    values.append([path,value])
                else:
                    list_values.append([path,value])

            for value in values:
                # if type(value) == type(None):
                #     value = 'None'
                csv_base += convert(value[1]) + ','

            #One list
            if len(list_values) == 1:
                if list_values[0][1]:
                    for val in list_values[0][1]:
                        outfile.write(csv_base + convert(val) + '\n')
                else:
                    outfile.write(csv_base + 'None' + '\n')

            #Two List
            elif len(list_values) == 2:
                if get_parent_path(list_values[0][0], json_keys) == get_parent_path(list_values[1][0], json_keys): #Handles mismatched sizes of lists from same parent.
                    #Same Parents
                    if len(list_values[0][1]) == len(list_values[1][1]):
                        if list_values[0][1]:
                            for i in range(len(list_values[0][1])):
                                outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + '\n')
                        else:
                            outfile.write(csv_base + ',None' + ',None' + '\n')

                    else:
                        if list_values[0][1]:
                            for val in list_values[0][1]:
                                
                                if list_values[1][1]:
                                    for val1 in list_values[1][1]:
                                        outfile.write(csv_base + convert(val) + ',' + convert(val1) + '\n')
                                else:
                                    outfile.write(csv_base + convert(val) + ',None' + '\n')
                        else:
                            if list_values[1]:
                                for val1 in list_values[1][1]:
                                        outfile.write(csv_base + 'None' + ',' + convert(val1) + '\n')
                                else:
                                    outfile.write(csv_base + 'None' + ',None' + '\n')

            elif len(list_values) == 3:
                #All lists come from same object
                if get_parent_path(list_values[0][0], json_keys) == get_parent_path(list_values[1][0], json_keys) == get_parent_path(list_values[2][0], json_keys): #Handles mismatched sizes of lists from same parent.
                    if len(list_values[0][1]) == len(list_values[1][1]) == len(list_values[2][1]):
                        if list_values[0][1]:
                            for i in range(len(list_values[0][1])):
                                outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][i]) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')

                    #One
                    if len(list_values[0][1]) == len(list_values[1][1]):
                        if list_values[0][1]:
                            if list_values[2][1]:
                                for i in range(len(list_values[0][1])):
                                    for j in range(len(list_values[2][1])):
                                        outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][j]) + '\n')
                            else:
                                for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + ',None' + '\n')
                        elif list_values[2][1]:
                            for i in range(len(list_values[2][1])):
                                    outfile.write(csv_base + 'None' + ',None' + convert(list_values[2][1][i]) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')


                    #Two
                    if len(list_values[0][1]) == len(list_values[2][1]):
                        if list_values[0][1]:
                            if list_values[1][1]:
                                for i in range(len(list_values[0][1])):
                                    for j in range(len(list_values[1][1])):
                                        outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][j]) + ',' + convert(list_values[2][1][i]) + '\n')
                            else:
                                for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',None' + convert(list_values[2][1][i]) + '\n')
                        elif list_values[1][1]:
                            for i in range(len(list_values[1][1])):
                                    outfile.write(csv_base + 'None' + convert(list_values[1][1][i]) + ',None' +  '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')
                        

                    #Three
                    if len(list_values[1][1]) == len(list_values[2][1]):
                        if list_values[1][1]:
                            if list_values[0][1]:
                                for i in range(len(list_values[1][1])):
                                    for j in range(len(list_values[0][1])):
                                        outfile.write(csv_base + convert(list_values[0][1][j]) + ',' + convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][i]) + '\n')
                            else:
                                for i in range(len(list_values[1][1])):
                                    outfile.write(csv_base + 'None', convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][i]) + '\n')
                        elif list_values[0][1]:
                            for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',None'  + ',None' +  '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')

                # 0,1
                elif get_parent_path(list_values[0][0], json_keys) == get_parent_path(list_values[1][0], json_keys):
                    if len(list_values[0][1]) == len(list_values[1][1]):
                        if list_values[0][1]:
                            if list_values[2][1]:
                                for i in range(len(list_values[0][1])):
                                    for j in range(len(list_values[2][1])):
                                        blah = csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][j]) + '\n'
                                        print(blah)
                                        outfile.write(blah)
                            else:
                                for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][i]) + ',None' + '\n')
                        elif list_values[2][1]:
                            for i in range(len(list_values[2][1])):
                                    outfile.write(csv_base + 'None' + ',None' + convert(list_values[2][1][i]) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')
                    else:
                        if list_values[0][1] and list_values[1][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    for val2 in list_values[2][1]:
                                        outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',' + convert(val2) + '\n')
                        elif list_values[0][1] and list_values[1][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',None' + '\n')
                        elif list_values[1][1] and list_values[2][1]:
                            for val in list_values[1][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + 'None' + ',' + convert(val) + ',' + convert(val1) + '\n')
                        elif list_values[0][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + convert(val) + ',None' + ',' + convert(val1) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')


                #1,2
                elif get_parent_path(list_values[1][0], json_keys) == get_parent_path(list_values[2][0], json_keys):
                    if len(list_values[1][1]) == len(list_values[2][1]):
                        if list_values[1][1]:
                            if list_values[0][1]:
                                for i in range(len(list_values[1][1])):
                                    for j in range(len(list_values[0][1])):
                                        outfile.write(csv_base + convert(list_values[0][1][j]) + ',' + convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][i]) + '\n')
                            else:
                                for i in range(len(list_values[1][1])):
                                    outfile.write(csv_base + 'None', convert(list_values[1][1][i]) + ',' + convert(list_values[2][1][i]) + '\n')
                        elif list_values[0][1]:
                            for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',None'  + ',None' +  '\n')
                        else:
                            outfile.write(csv_base + ',None' + ',None' + ',None' + '\n')
                    else:
                        if list_values[0][1] and list_values[1][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    for val2 in list_values[2][1]:
                                        outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',' + convert(val2) + '\n')
                        elif list_values[0][1] and list_values[1][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',None' + '\n')
                        elif list_values[1][1] and list_values[2][1]:
                            for val in list_values[1][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + 'None' + ',' + convert(val) + ',' + convert(val1) + '\n')
                        elif list_values[0][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + convert(val) + ',None' + ',' + convert(val1) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')
                #0,2
                elif get_parent_path(list_values[0][0], json_keys) == get_parent_path(list_values[2][0], json_keys):
                    if len(list_values[0][1]) == len(list_values[2][1]):
                        if list_values[0][1]:
                            if list_values[1][1]:
                                for i in range(len(list_values[0][1])):
                                    for j in range(len(list_values[1][1])):
                                        outfile.write(csv_base + convert(list_values[0][1][i]) + ',' + convert(list_values[1][1][j]) + ',' + convert(list_values[2][1][i]) + '\n')
                            else:
                                for i in range(len(list_values[0][1])):
                                    outfile.write(csv_base + convert(list_values[0][1][i]) + ',None' + convert(list_values[2][1][i]) + '\n')
                        elif list_values[1][1]:
                            for i in range(len(list_values[1][1])):
                                    outfile.write(csv_base + ',None' + convert(list_values[1][1][i]) + ',None' +  '\n')
                        else:
                            outfile.write(csv_base + ',None' + ',None' + ',None' + '\n')
                    else:
                        if list_values[0][1] and list_values[1][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    for val2 in list_values[2][1]:
                                        outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',' + convert(val2) + '\n')
                        elif list_values[0][1] and list_values[1][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[1][1]:
                                    outfile.write(csv_base + convert(val) + ',' + convert(val1) + ',None' + '\n')
                        elif list_values[1][1] and list_values[2][1]:
                            for val in list_values[1][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + 'None' + ',' + convert(val) + ',' + convert(val1) + '\n')
                        elif list_values[0][1] and list_values[2][1]:
                            for val in list_values[0][1]:
                                for val1 in list_values[2][1]:
                                    outfile.write(csv_base + convert(val) + ',None' + ',' + convert(val1) + '\n')
                        else:
                            outfile.write(csv_base + 'None' + ',None' + ',None' + '\n')

                else:
                    #TODO Needs work here. if one value is empty the other should still be written and vice versa
                    #Different Path
                    if list_values[0][1]:
                        for val in list_values[0][1]:
                            if list_values[1][1]:
                                for val1 in list_values[1][1]:
                                    outfile.write(csv_base + convert(val) + ',' + convert(val1) + '\n')
                            else:
                                outfile.write(csv_base + convert(val) + ',None' + '\n')
                    else:
                        if list_values[1]:
                            for val1 in list_values[1][1]:
                                    outfile.write(csv_base + 'None' + ',' + convert(val1) + '\n')
                            else:
                                outfile.write(csv_base + 'None' + ',None' + '\n')
            else:
                outfile.write(csv_base + '\n')

#==================================================================================================

if __name__ == '__main__':
    from loguru import logger 
    loguru_logger = logger

    fields_supplied = True
    endpoint = ''
    if '-endpoint' not in sys.argv:
        loguru_logger.error('Error: Missing endpoint argument. Exiting...')
        exit()
    if '-fields' not in sys.argv:
        loguru_logger.warning('Missing fields argument. Displaying options...')
        fields_supplied = False
        
    try:
        endpoint = sys.argv[sys.argv.index('-endpoint') + 1]
    except:
        loguru_logger.error('Error: Missing endpoint argument value. Exiting...')
        exit()
    
    session_manager = session_loader.onprem_load_from_file(logger=loguru_logger)
    cwp_session = session_manager.create_cwp_session()
    res = cwp_session.request('GET', endpoint)
    json_template =[]
    get_object_keys(json_template, res.json()[0], '', '', '') #Used to validate fields
    json_data = res.json()

    fields = []

    #If not fields are supplied, let the user select in realtime
    if fields_supplied == False:
        print_paths(json_template)
        print()
        fields_input = input('Enter path names, space separated: ')
        fields = fields_input.split(' ')   
    else:
        try:
            fields_raw = sys.argv[sys.argv.index('-fields') + 1]
            fields = fields_raw.split(' ')
            res = validate_fields(fields, json_template)
            if res != True:
                loguru_logger.error('Error: Invalid field format. Exiting...')
                exit()
        except:
            loguru_logger.error('Error: Missing fields argument value. Exiting...')
            exit()

    build_csv('out.csv',fields, json_template, json_data)


    #Sort fields to have array data at the end



    





