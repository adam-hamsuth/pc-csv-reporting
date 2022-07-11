import session_manager
import json
import os.path as path

if __name__ == '__main__':
    sessions = session_manager.load_config_create_session(file_mode=True, num_tenants=1)

    session = sessions[0]

    res = session.request('GET', 'cloud/aws/161085564623/project')
    alert_data = res.json()

    with open('cloud_dump.json', 'w') as outfile:
        json.dump(alert_data, outfile)
