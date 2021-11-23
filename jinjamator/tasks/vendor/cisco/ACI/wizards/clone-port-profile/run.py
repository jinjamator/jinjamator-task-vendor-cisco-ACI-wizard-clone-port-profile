# Copyright 2021 Wilhelm Putz

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from time import sleep
from pprint import pprint
port_number_re=re.compile(r'\d+')
po_number_re=re.compile(r'\d+')
slot_number_re=re.compile(r'e\d+')

remove_hport_children=[]


# for vpc_domain in cisco.aci.query('/api/node/class/vpcDom.json')['imdata']:
#     attr=vpc_domain['vpcDom']['attributes']
#     log.info(attr['dn'].split('/')[2][5:])

# import sys
# sys.exit(0)



def clone_accportgrp(src_dn,dst_dn):
    if src_dn == dst_dn:
        log.info(f'skipping clone of source to itself. {src_dn}')
        return None
    log.debug(f"clone obj {src_dn} -> {dst_dn}")
    src_data=cisco.aci.query(f"/api/node/mo/{src_dn}.json?rsp-subtree=full&rsp-prop-include=config-only")
    obj_type=list(src_data['imdata'][0].keys())[0]
    src_data['imdata'][0][obj_type]['attributes']['dn']=dst_dn
    src_data['imdata'][0][obj_type]['attributes']['name']='-'.join(dst_dn.split('/')[-1].split('-')[1:])
    
    self.configuration['data']=json.dumps(src_data)
    sleep(0.5)
    task.run('.helper/send_data.j2',self.configuration)
    

def convert_portgrp_dn(src_dn, target_policy_group_name):
    obj_name=src_dn.split('/')[3]
    tmp=obj_name.split(separator)
    obj_type=tmp[0]
    invalid=True
    
    if obj_type == "accportgrp" and port_number_re.match(tmp[-1]) and slot_number_re.match(tmp[-2]):
        log.info(f'Access Port detected {src_dn}')
        invalid=False
    if obj_type == "accbundle" and po_number_re.match(tmp[-1]) and tmp[-2].lower() == 'po':
        log.info(f'Port-channel Port detected {src_dn}')
        invalid=False
    if obj_type == "accbundle" and po_number_re.match(tmp[-1]) and tmp[-2].lower() == 'vpc':
        log.info(f'VPC Port detected {src_dn}')
        path_prefix='/'.join(src_dn.split('/')[:3])
        target_dn=f"{path_prefix}/{obj_type}{separator}{vpc_target_policy_group_name}{separator}{tmp[-2]}{separator}{tmp[-1]}"
        return target_dn
        invalid=False
    
    if invalid:
        log.warning(f"invalid naming detected {tmp} -> keeping src_dn")
        return src_dn
    path_prefix='/'.join(src_dn.split('/')[:3])
    target_dn=f"{path_prefix}/{obj_type}{separator}{target_policy_group_name}{separator}{tmp[-2]}{separator}{tmp[-1]}"

    return target_dn

vpc_lookup_table={}



source_type = None
base_data=cisco.aci.query(f"/api/node/mo/uni/infra/accportprof-{source_policy_group_name}.json?rsp-subtree=full&rsp-prop-include=config-only")["imdata"]
if not base_data:
    base_data=cisco.aci.query(f"/api/node/mo/uni/infra/fexprof-{source_policy_group_name}.json?rsp-subtree=full&rsp-prop-include=config-only")["imdata"]
for base_obj in base_data:
    
    base_obj_type=list(base_obj.keys())[0]

    if base_obj_type == "infraAccPortP":
        log.info("Source is a leaf switch")
        source_type="leaf"
    elif base_obj_type == "infraFexP":
        log.info("Source is a FEX")
        source_type="fex"
    else:
        raise ValueError(f"Unsupported base object type {base_obj_type} only infraAccPortP or infraFexP supported.")

    for hport_idx,infra_hports in enumerate(base_obj[base_obj_type]['children']):


        for idx,accportgrp in enumerate(infra_hports.get('infraHPortS',{}).get('children',[])):

            if not "infraRsAccBaseGrp" in accportgrp:
                log.info(f"skipping {list(accportgrp.keys())[0]}")
                continue
            target_portgrp_dn=convert_portgrp_dn(accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"],target_policy_group_name)
            if '/fexbundle-' in target_portgrp_dn and target_type == 'fex':
                log.warning('Cannot attach FEX on FEX -> skipping')
                remove_hport_children.append(hport_idx)
                continue
            clone_accportgrp(accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"],target_portgrp_dn)            
            accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"]=target_portgrp_dn
    
    for idx in remove_hport_children:
        del base_obj[base_obj_type]['children'][idx]
    base_obj[base_obj_type]['attributes']['name']=target_policy_group_name
    if target_type == "fex":
        tmp=base_obj[base_obj_type]
        del base_obj[base_obj_type]
        base_obj["infraFexP"]=tmp
        base_obj['infraFexP']['attributes']['dn']=f'uni/infra/fexprof-{target_policy_group_name}'
        base_obj["infraFexP"]['attributes']['dn']=f'uni/infra/fexprof-{target_policy_group_name}'
        if source_type == "leaf":
            base_obj["infraFexP"]["children"].append(
                json.loads('{"infraFexBndlGrp":{"attributes":{"annotation":"","descr":"","dn":"uni/infra/fexprof-' + target_policy_group_name + '/fexbundle-' + target_policy_group_name + '","name":"' +target_policy_group_name+ '","nameAlias":"","ownerKey":"","ownerTag":"","userdom":":all:"},"children":[{"infraRsMonFexInfraPol":{"attributes":{"annotation":"","tnMonInfraPolName":"","userdom":"all"}}}]}}')
            )

    else:
        tmp=base_obj[base_obj_type]
        del base_obj[base_obj_type]
        base_obj["infraAccPortP"]=tmp
        base_obj["infraAccPortP"]['attributes']['dn']=f'uni/infra/accportprof-{target_policy_group_name}'
        children_to_delete=[]
        for idx,child in enumerate(base_obj["infraAccPortP"].get("children",[])):
            if "infraFexBndlGrp" in child:
                children_to_delete.append(idx)
        for i in children_to_delete:
            del base_obj["infraAccPortP"]["children"][idx]

    return {'imdata':[base_obj]}
