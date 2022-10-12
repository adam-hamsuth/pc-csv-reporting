from pcpi import session_loader
from loguru import logger
import sys
import jmespath

def get_parent_path(path):
    if '.' in path:
        args = path.split('.')
        parent_args = args[:-1]
        parent_path = ''
        for arg in parent_args:
            parent_path += arg
        
        if len(parent_path) >= 3:
            if parent_path[:-3] == '[*]':
                parent_path = parent_path[:-3]
            if parent_path[:-2] == '[]':
                parent_path = parent_path[:-2]
            if parent_path[-3] == '[' and parent_path[-1] == ']':
                parent_path = parent_path[:-3]
        return parent_path
    else:
        return path

def build_csv(json_data, paths):
    for blob in json_data:
        results = []
        for path in paths:
            value = jmespath.search(path, blob)
            results.append([value, get_parent_path(path)])

        parent_fields = []
        for path in paths:
            parent_fields.append(get_parent_path(path))
        fields_with_same_parent = []
        for i in range(len(parent_fields)):
            if parent_fields.count(parent_fields[i]) > 1:
                fields_with_same_parent.append([parent_fields[i],i])

        fields_with_same_parent_names = []
        for f in fields_with_same_parent:
            fields_with_same_parent_names.append(f[0])

        print(fields_with_same_parent)


        print(results)
        print()
        print()

        strings = []
        shared_lists = {} #TODO Put all lists here, the ones with same parents will be grouped and the singletons will not be.
        #TODO then just iterate over the shared list, output same parents together, output singles not together
        lists = []
        for res in results:
            if type(res[0]) == type(""):
                strings.append(res[0])
            if res[1] in fields_with_same_parent_names:
                curr_list = shared_lists.get(res[1])
                print(f"curr_list_old:{res[1]}", curr_list)
                if curr_list:
                    curr_list.append(res[0])
                    shared_lists.update({res[1]:curr_list})
                else:
                    shared_lists.update({res[1]:[res[0]]})
                curr_list = shared_lists.get(res[1])
                print(f"curr_list_new:{res[1]}", curr_list)
            else:
                lists.append(res[0])
                

        print(shared_lists)




if __name__ == '__main__':
    from loguru import logger 
    loguru_logger = logger

    fields_supplied = True
    endpoint = ''
    if '-endpoint' not in sys.argv:
        loguru_logger.error('Error: Missing endpoint argument. Exiting...')
        exit()
    if '-fields' not in sys.argv:
        loguru_logger.error('Error: Missing fields argument. Exiting...')
        exit()
    try:
        endpoint = sys.argv[sys.argv.index('-endpoint') + 1]
    except:
        loguru_logger.error('Error: Missing endpoint argument value. Exiting...')
        exit()
    fields = []
    try:
        fields_raw = sys.argv[sys.argv.index('-fields') + 1]
        fields = fields_raw.split(' ')
    except:
        loguru_logger.error('Error: Missing fields argument value. Exiting...')
        exit()
        
    
    session_manager = session_loader.onprem_load_from_file(logger=loguru_logger)
    cwp_session = session_manager.create_cwp_session()
    res = cwp_session.request('GET', endpoint)
    data = res.json()


    build_csv(data, fields)