from os import path
import os
import re
import yaml
import requests
import json
import time
from loguru import logger

def c_print(*args, **kwargs):
    '''
    Uses ascii codes to enable colored print statements. Works on Mac, Linux and Windows terminals
    '''

    #Magic that makes colors work on windows terminals
    os.system('')
    
    #Define Colors for more readable output
    c_gray = '\033[90m'
    c_red = '\033[91m'
    c_green = '\033[92m'
    c_yellow = '\033[93m'
    c_blue = '\033[94m'
    c_end = '\033[0m'

    color = c_end
    if 'color' in kwargs:
        c = kwargs['color'].lower()
        if c == 'gray' or c == 'grey':
            color = c_gray
        elif c ==  'red':
            color = c_red
        elif c == 'green':
            color = c_green
        elif c == 'yellow':
            color = c_yellow
        elif c == 'blue':
            color = c_blue
        else:
            color = c_end

    _end = '\n'
    if 'end' in kwargs:
        _end = kwargs['end']

    print(f'{color}', end='')
    for val in args:
        print(val, end='')
    print(f'{c_end}', end=_end)

#==============================================================================

def validate_credentials(a_key, s_key, url) -> bool:
    '''
    This function creates a session with the supplied credentials to test 
    if the user successfully entered valid credentails.
    '''

    headers = {
    'content-type': 'application/json; charset=UTF-8'
    }

    payload = {
        "username": f"{a_key}",
        "password": f"{s_key}"
    }

    try:
        c_print('API - Validating credentials')
        response = requests.request("POST", f'{url}/login', headers=headers, json=payload)

        if response.status_code == 200:
            c_print('SUCCESS', color='green')
            print()
            return True
        else:
            return False
    except:
        c_print('ERROR', end=' ', color='red')
        print('Could not connect to Prisma Cloud API.')
        print()
        print('Steps to troubleshoot:')
        c_print('1) Please disconnect from any incompatible VPN', color='blue')
        print()
        c_print('2) Please ensure you have entered a valid Prisma Cloud URL.', color='blue')
        print('EX: https://app.prismacloud.io or https://app2.eu.prismacloud.io')
        print()
        return False

#==============================================================================

def validate_url(url):
    if len(url) >= 3:
        if 'https://' not in url:
            if url[:3] == 'app' or url[:3] == 'api':
                url = 'https://' + url
            
    
    url = url.replace('app', 'api')

    url = re.sub(r'prismacloud\.io\S*', 'prismacloud.io', url)

    return url

#==============================================================================

def get_tenant_credentials():

    c_print('Enter tenant name or any preferred identifier:', color='blue')
    name = input()

    c_print('Enter tenant url. (ex: https://app.ca.prismacloud.io):', color='blue')
    url = input()
    print()
    new_url = validate_url(url)
    if new_url != url:
        c_print('Adjusted URL:',color='yellow')
        print(new_url)
        print()

    c_print('Enter tenant access key:', color='blue')
    a_key = input()
    print()

    c_print('Enter tenant secret key:', color='blue')
    s_key = input()
    print()
    

    return name, a_key, s_key, new_url

#==============================================================================

def build_session_dict(name, a_key, s_key, url):
    session_dict = {
        name: {
            'access_key': a_key,
            'secret_key': s_key,
            'api_url': url
            }
    }
    return session_dict

#==============================================================================

def get_credentials_from_user(num_tenants):
    #Gets the source tenant credentials and ensures that are valid
    credentials = []

    if num_tenants != -1:
        for i in range(num_tenants):
            valid = False
            while not valid:
                c_print('Enter credentials for the tenant', color='blue')
                print()
                src_name, src_a_key, src_s_key, src_url = get_tenant_credentials()
                
                valid = validate_credentials(src_a_key, src_s_key, src_url)
                if valid == False:
                    c_print('FAILED', end=' ', color='red')
                    print('Invalid credentails. Please re-enter your credentials')
                    print()
                else:
                    credentials.append(build_session_dict(src_name, src_a_key, src_s_key, src_url))

        return credentials
    else:
        while True:
            valid = False
            while not valid:
                c_print('Enter credentials for the tenant', color='blue')
                print()
                src_name, src_a_key, src_s_key, src_url = get_tenant_credentials()
                
                valid = validate_credentials(src_a_key, src_s_key, src_url)
                if valid == False:
                    c_print('FAILED', end=' ', color='red')
                    print('Invalid credentails. Please re-enter your credentials')
                    print()
                else:
                    credentials.append(build_session_dict(src_name, src_a_key, src_s_key, src_url))
            
            c_print('Would you like to add an other tenant? Y/N')
            choice = input().lower()

            if choice != 'yes' and choice != 'y':
                break

        return credentials


def load_yaml(file_name, logger):
    with open(file_name, "r") as file:
        cfg = yaml.load(file, Loader=yaml.BaseLoader)

    credentials = cfg['credentials']
    mode = cfg['mode']
    modes = json.loads(cfg['modes'])
    #Parse cfg for tenant names and create tokens for each tenant
    tenant_sessions = []
    for tenant in credentials:
        tenant_name = ''
        tenant_keys = tenant.keys()
        for name in tenant_keys:
            tenant_name = name     

        a_key = tenant[tenant_name]['access_key']
        s_key = tenant[tenant_name]['secret_key']
        api_url = tenant[tenant_name]['api_url']

        tenant_sessions.append(Session(tenant_name, a_key, s_key, api_url, logger))

    return tenant_sessions, mode, modes

def load_uuid_yaml(file_name, logger):
    with open(file_name, "r") as file:
        cfg = yaml.load(file, Loader=yaml.BaseLoader)

    credentials = cfg['credentials']
    entity_type = cfg['type']
    uuid = cfg['uuid']
    cmp_type = cfg['cmp_type']

    tenant_sessions = []
    for tenant in credentials:
        tenant_name = ''
        tenant_keys = tenant.keys()
        for name in tenant_keys:
            tenant_name = name     

        a_key = tenant[tenant_name]['access_key']
        s_key = tenant[tenant_name]['secret_key']
        api_url = tenant[tenant_name]['api_url']

        tenant_sessions.append(Session(tenant_name, a_key, s_key, api_url, logger))

    return tenant_sessions, entity_type, uuid, cmp_type

def load_config_create_session(file_mode, logger=logger, num_tenants=-1):
    '''
    Reads config.yml and generates a Session object for the tenant

    Returns:
    Tenant Session object
    '''

    if file_mode:
        #Open and load config file
        if not path.exists('tenant_credentials.yml'):
            #Create credentials yml file
            c_print('No credentials file found. Generating...', color='yellow')
            print()
            tenants = get_credentials_from_user(num_tenants)
            with open('tenant_credentials.yml', 'w') as yml_file:
                for tenant in tenants:
                    yaml.dump(tenant, yml_file, default_flow_style=False)

        with open("tenant_credentials.yml", "r") as file:
            cfg = yaml.load(file, Loader=yaml.BaseLoader)

        #Parse cfg for tenant names and create tokens for each tenant
        tenant_sessions = []
        for tenant in cfg:
            a_key = cfg[tenant]['access_key']
            s_key = cfg[tenant]['secret_key']
            api_url = cfg[tenant]['api_url']

            tenant_sessions.append(Session(tenant, a_key, s_key, api_url, logger))

        return tenant_sessions
    else:
        tenant_sessions = []
        tenants = get_credentials_from_user(num_tenants)
        for tenant in tenants:
            for key in tenant:
                name = key

                tenant_sessions.append(Session(name, tenant[name]['access_key'], tenant[name]['secret_key'], tenant[name]['api_url'], logger))

        return tenant_sessions

class Session:
    def __init__(self, tenant_name: str, a_key: str, s_key: str, api_url: str, logger: object):
        """
        Initializes a Prisma Cloud API session for a given tenant.

        Keyword Arguments:
        tenant_name -- Name of tenant associated with session
        a_key -- Tenant Access Key
        s_key -- Tenant Secret Key
        api_url -- API URL Tenant is hosted on
        """
        self.logger = logger
        self.tenant = tenant_name
        self.a_key = a_key
        self.s_key = s_key
        self.api_url = api_url
        self.prismaId = ''
        self.token = self.api_login()
        self.headers = {
            'content-type': 'application/json; charset=UTF-8',
            'x-redlock-auth': self.token
            }
        self.retries = 6
        self.retry_statuses = [401, 429, 500, 502, 503, 504]
        self.rate_limit = 429
        if self.token != 'BAD':
            logger.info(f'Session created for tenant: {tenant_name}')
        else:
            logger.error(f'Session creation failed for tenant: {tenant_name}')
            logger.info('Exiting...')
            quit()

#==============================================================================

    def api_login(self) -> None:
        '''
        Calls the Prisma Cloud API to generate a x-redlock-auth JWT.

        Returns:
        x-redlock-auth JWT.
        '''

        #Build request
        url = f'{self.api_url}/login'
        
        headers = {
            'content-type': 'application/json; charset=UTF-8'
            }

        payload = {
            "username": f"{self.a_key}",
            "password": f"{self.s_key}"
        }

        self.logger.debug('API - Generating session token.')
        response = object()
        try:
            response = requests.request("POST", url, headers=headers, json=payload)
        except:
            self.logger.error('Failed to connect to API.')
            self.logger.warning('Make sure any offending VPNs are disabled.')
            self.logger.info('Exiting...')
            quit()


        #Results
        if response.status_code == 200:
            self.logger.success('SUCCESS')
            data = response.json()
            self.prismaId = data.get('customerNames')[0].get('prismaId')

            token = data.get('token')
            self.token = token
            self.headers = {
            'content-type': 'application/json; charset=UTF-8',
            'x-redlock-auth': token
            }
            
            return token
        elif response.status_code == 401:
            self.logger.error('FAILED')
            self.logger.warning('Invalid Login Credentials. JWT not generated.')
            self.token = 'BAD'
            return 'BAD'
        else:
            self.logger.error('FAILED')
            self.logger.error('ERROR Logging In. JWT not generated.')
            self.token = 'BAD'

            self.logger.warning('RESPONSE:')
            self.logger.info(response)
            self.logger.warning('RESPONSE URL:')
            self.logger.info(response.url)
            self.logger.warning('RESPONSE TEXT:')
            self.logger.info(response.text)
            
            return 'BAD'

#==============================================================================

    def api_call_wrapper(self, method: str, url: str, json: dict=None, data: dict=None, params: dict=None, redlock_ignore: list=None, status_ignore: list=[]):
        """
        A wrapper around all API calls that handles token generation, retrying
        requests and API error console output logging.

        Keyword Arguments:
        method -- Request method/type. Ex: POST or GET
        url -- Full API request URL
        data -- Body of the request in a json compatible format
        params -- Queries for the API request

        Returns:
        Respose from API call.

        """
        self.logger.debug(f'{url}')
        res = self.request_wrapper(method, url, headers=self.headers, json=json, data=data, params=params)
        
        if res.status_code == 200 or res.status_code in status_ignore:
            self.logger.success('SUCCESS')
            return res
        
        # if res.status_code == 401:
        #     self.logger.warning('Token expired. Generating new Token and retrying.')
        #     self.api_login()
        #     self.logger.debug(f'{url}')
        #     res = requests.request(method, url, headers=self.headers, json=json, data=data, params=params)

        retries = 0
        while res.status_code in self.retry_statuses and retries < self.retries:
            if res.status_code == self.rate_limit:
                time.sleep(2)
            if res.status_code == 401:
                self.logger.warning('Token expired. Generating new Token and retrying.')
                self.api_login()
            self.logger.warning(f'Retrying request. Code {res.status_code}.')
            self.logger.debug(f'{url}')
            res = self.request_wrapper(method, url, headers=self.headers, json=json, data=data, params=params)
            retries += 1
        
        if res.status_code == 200 or res.status_code in status_ignore:
            self.logger.success('SUCCESS')
            return res

        #Some redlock errors need to be handled elsewhere and don't require this debugging output
        if 'x-redlock-status' in res.headers and redlock_ignore:
            for el in redlock_ignore:
                if el in res.headers['x-redlock-status']:
                    return res

        self.logger.error('FAILED')
        self.logger.error('REQUEST DUMP:')
        self.logger.warning('REQUEST HEADERS:')
        self.logger.info(self.headers)
        self.logger.warning('REQUEST JSON:')
        self.logger.info(json)
        if data:
            self.logger.warning('REQUEST DATA:')
            self.logger.info(data)
        self.logger.warning('REQUEST PARAMS:')
        self.logger.info(params)
        self.logger.warning('RESPONSE:')
        self.logger.info(res)
        self.logger.warning('RESPONSE URL:')
        self.logger.info(res.url)
        self.logger.warning('RESPONSE HEADERS:')
        self.logger.info(res.headers)
        self.logger.warning('RESPONSE REQUEST BODY:')
        self.logger.info(res.request.body)
        self.logger.warning('RESPONSE STATUS:')
        if 'x-redlock-status' in res.headers:
            self.logger.info(res.headers['x-redlock-status'])
        self.logger.warning('RESPONSE TEXT:')
        self.logger.info(res.text)
        self.logger.warning('RESPONSE JSON:')
        if res.text != "":
            for json_data in res.json():
                self.logger.info(json_data)

        return res

#==============================================================================

    def request(self, method: str, endpoint_url: str, json: dict=None, data: dict=None, params: dict=None, redlock_ignore: list=None, status_ignore: list=[]):
        '''
        Function for calling the PC API using this session manager. Accepts the
        same arguments as 'requests.request' minus the headers argument as 
        headers are supplied by the session manager.
        '''
        #Validate method
        method = method.upper()
        if method not in ['POST', 'PUT', 'GET', 'OPTIONS', 'DELETE', 'PATCH']:
            self.logger.warning('Invalid method.')
        
        #Build url
        if endpoint_url[0] != '/':
            endpoint_url = '/' + endpoint_url

        url = f'{self.api_url}{endpoint_url}'

        #Call wrapper
        return self.api_call_wrapper(method, url, json=json, data=data, params=params, redlock_ignore=redlock_ignore, status_ignore=status_ignore)


    def request_wrapper(self, method, url, headers, json, data, params):
        counter = 1
        r = ''
        while r == '' and counter < self.retries:
            counter += 1
            try:
                r = requests.request(method, url, headers=headers, json=json, data=data, params=params)
                return r
            except:
                self.logger.error('Request failed, retrying...')
                time.sleep(3)
                continue
            

        return requests.request(method, url, headers=headers, json=json, data=data, params=params)