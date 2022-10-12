from pcpi import session_loader
import json
import os.path as path

if __name__ == '__main__':
    session_manager = session_loader.load_from_env()

    session = session_manager.create_cspm_session()


    res = session.request('GET', 'v2/alert/rule')
    alert_data = res.json()

    res = session.request('GET', 'cloud/group')
    account_group_data = res.json()

    res = session.request('GET', 'cloud')
    cloud_account_data = res.json()

    res = session.request('GET', 'policy')
    policy_data = res.json()

    #HEADERS
    #Alert Rule Name, Policy ID, Policy Name, Account Group ID, Account Group Name, Cloud Account ID, Cloud Account Name


    # Alert Rules to Policies IDs----------------------------------------------
    out_path = path.join('output','alert_rules_to_policy_ids.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Alert Rule Name,Policy ID\n')
        for alr in alert_data:
            for plc in alr['policies']:
                outfile.write(alr['name'] + ',' + plc + '\n')

    # Alert Rules to EXCLUDED Policies IDs-------------------------------------
    out_path = path.join('output','alert_rules_to_excluded_policy_ids.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Alert Rule Name,Excluded Policy ID\n')
        for alr in alert_data:
            for plc in alr['excludedPolicies']:
                outfile.write(alr['name'] + ',' + plc + '\n')

    #Alert Rules to Enabled----------------------------------------------------
    out_path = path.join('output','alert_rules_to_enabled_ids.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Alert Rule Name,Alert Rule Enabled\n')
        for alr in alert_data:
            outfile.write(alr['name'] + ',' + str(alr['enabled']) + '\n')

    # Alert Rules to Account Groups IDs----------------------------------------
    out_path = path.join('output','alert_rules_to_account_group_ids.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Alert Rule Name, Account Group ID\n')
        for alr in alert_data:
            for acc_grp in alr['target'].get('accountGroups'):
                outfile.write(alr['name'] + ',' + acc_grp + '\n')

    # Account Group IDs to Cloud Account IDs-----------------------------------
    out_path = path.join('output','account_group_ids_to_cloud_account_ids.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Account Group ID,Cloud Account ID\n')
        for acc_grp in account_group_data:
            for cld_acc in acc_grp['accountIds']:
                outfile.write(acc_grp['id'] + ',' + cld_acc + '\n')

    # Policy IDs to Policy details-----------------------------------------------
    out_path = path.join('output','policy_ids_to_policy_details.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Policy ID,Policy Name, Policy Type, Policy Sub Type\n')
        for plc in policy_data:
            for plc_sub in plc['policySubTypes']:
                outfile.write(plc['policyId'] + ',' + plc['name'] + ',' + plc['policyType'] +  ',' +plc_sub + '\n')


    # Account Group IDs to Account Group Names---------------------------------
    out_path = path.join('output','account_group_ids_to_account_group_names.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Account Group ID,Account Group Name\n')
        for acc_grp in account_group_data:
            outfile.write(acc_grp['id'] + ',' + acc_grp['name'] + '\n')

    # Cloud Account IDs to Cloud Account Details---------------------------------
    out_path = path.join('output','cloud_account_ids_to_cloud_account_details.csv')
    with open(out_path, 'w') as outfile:
        outfile.write('Cloud Account ID,Cloud Account Name,Cloud Type,Account Type\n')
        for cld_acc in cloud_account_data:
            acc_id = ''
            acc_type = 'None'
            acc_name = ''
            cld_type = ''
            if 'cloudAccount' in cld_acc:
                #Set variables
                cld_type = cld_acc['cloudAccount']['cloudType']
                acc_name = cld_acc['cloudAccount']['name']
                acc_id = cld_acc['cloudAccount']['accountId']
            else:
                #Set variables
                cld_type = cld_acc['cloudType']
                acc_type = cld_acc['accountType']
                acc_name = cld_acc['name']
                acc_id = cld_acc['accountId']
            
            outfile.write(acc_id + ',' + acc_name + ',' + cld_type + ',' + acc_type + '\n')

            





    # account_groups_policies_dict = {}
    # account_groups_alert_rule_dict = {}

    # for alert_rule in alert_data:
    #     policies_set = set(alert_rule['policies'])
    #     enabled = alert_rule['enabled']

    #     account_groups_alert_rule_dict.update({alert_rule['name']: {'enabled':enabled, 'accountGroups': alert_rule['target']['accountGroups']}})

    #     if enabled:
    #         for acc_grp in alert_rule['target']['accountGroups']:
    #             acc_grp_dict = account_groups_policies_dict.get(acc_grp)
    #             if acc_grp_dict:
    #                 curr_policies = acc_grp_dict['policies']
    #                 for el in curr_policies:
    #                     policies_set.add(el)

    #             account_groups_policies_dict.update({acc_grp: {
    #                 'policiesCount': len(policies_set),
    #                 'policies': list(policies_set)
    #                 }
    #             })

    # with open('account_groups_policies.csv', 'w') as outfile:
    #     outfile.write('accountGroup,policies\n')
        
    #     for acc in account_groups_policies_dict.keys():
    #         account_group = acc
    #         policy_count = account_groups_policies_dict[acc]['policiesCount']
    #         policies = account_groups_policies_dict[acc]['policies']

    #         for plc in policies:
    #             outfile.write(account_group + ',' + plc + '\n')
            
    #         if len(policies) == 0:
    #             outfile.wite(account_group + ',' + 'none\n')

    # with open('account_group_alert_rules.csv', 'w') as outfile:
    #     outfile.write('name,enabled,accountGroup\n')

    #     for alr in account_groups_alert_rule_dict.keys():
    #         name = alr
    #         enabled = account_groups_alert_rule_dict[alr]['enabled']
    #         account_groups = account_groups_alert_rule_dict[alr]['accountGroups']

    #         for acc in account_groups:
    #             outfile.write(name + ',' + str(enabled) + ',' + acc + '\n')

    #         if len(account_groups) == 0:
    #             outfile.write(name + ',' + str(enabled) + ',' + 'none' + '\n')