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
    task.run('helper/send_data.j2',self.configuration)
    

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
        invalid=False
    
    if invalid:
        log.warning(f"invalid naming detected {tmp} -> keeping src_dn")
        return src_dn
    path_prefix='/'.join(src_dn.split('/')[:3])
    target_dn=f"{path_prefix}/{obj_type}{separator}{target_policy_group_name}{separator}{tmp[-2]}{separator}{tmp[-1]}"

    return target_dn

# /api/node/class/infraFexP.json
# /api/node/class/infraAccPortP.json



base_data=cisco.aci.query(f"/api/node/mo/uni/infra/accportprof-{source_policy_group_name}.json?rsp-subtree=full&rsp-prop-include=config-only")["imdata"]
if not base_data:
    base_data=cisco.aci.query(f"/api/node/mo/uni/infra/fexprof-{source_policy_group_name}.json?rsp-subtree=full&rsp-prop-include=config-only")["imdata"]
for base_obj in base_data:
    
    base_obj_type=list(base_obj.keys())[0]
    if base_obj_type not in  [ 'infraAccPortP' ]:
        raise (f"Unsupported base object type {base_obj_type}")

    for hport_idx,infra_hports in enumerate(base_obj[base_obj_type]['children']):
        if not "infraHPortS" in infra_hports:
            raise ValueError(f"Unexpected Object {infra_hports}")
        for idx,accportgrp in enumerate(infra_hports['infraHPortS'].get('children',[])):
        
            if not "infraRsAccBaseGrp" in accportgrp:
                log.info(f"skipping {list(accportgrp.keys())[0]}")
                continue
            target_portgrp_dn=convert_portgrp_dn(accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"],target_policy_group_name)
            if '/fexbundle-' in target_portgrp_dn and target_type == 'fex':
                log.error('Cannot attach FEX on FEX -> skipping')
                remove_hport_children.append(hport_idx)
                continue
            clone_accportgrp(accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"],target_portgrp_dn)
            # infra_hports['infraHPortS'][idx]['infraRsAccBaseGrp']["attributes"]["tDn"]=
            
            accportgrp['infraRsAccBaseGrp']["attributes"]["tDn"]=target_portgrp_dn

            # task.run('helper/clone_accportgrp.j2')
    for idx in remove_hport_children:
        del base_obj[base_obj_type]['children'][idx]
    base_obj[base_obj_type]['attributes']['name']=target_policy_group_name
    if target_type == "fex":
        tmp=base_obj[base_obj_type]
        del base_obj[base_obj_type]
        base_obj["infraFexP"]=tmp
        base_obj['infraFexP']['attributes']['dn']=f'uni/infra/fexprof-{target_policy_group_name}'
        base_obj["infraFexP"]['attributes']['dn']=f'uni/infra/fexprof-{target_policy_group_name}'
    else:
        tmp=base_obj[base_obj_type]
        del base_obj[base_obj_type]
        base_obj["infraAccPortP"]=tmp
        base_obj["infraAccPortP"]['attributes']['dn']=f'uni/infra/accportprof-{target_policy_group_name}'
    return {'imdata':[base_obj]}
