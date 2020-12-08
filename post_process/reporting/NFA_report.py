from glob import glob
import numpy as np
import pandas as pd
import json
import os

def NFA_report(paths_dict):
    files = glob(os.path.join(paths_dict["event"],'MTK*.json'))

    faceData = np.genfromtxt(os.path.join(paths_dict["root"], 'simcoords5DMPI.txt'),
                         dtype=("U30", float, float, float, float, float))

    myfaces = [fc.split('/')[-1] for fc in faceData['f0']]

    #Load MDS data
    mds = np.loadtxt(open(os.path.join(paths_dict["root"], 'mds.csv'), 'r'), delimiter=',')

    #Num neighbors vs. probability correct recall
    thresh = 0.88
    numneighbors = np.sum(mds<thresh, axis=0)

    bins = np.linspace(0, 1.2, 11)

    #Load subject data from json files
    sub_data = []
    for f in files:
        sd = json.load(open(f))
        
        block = 1
        study_trial = 1
        recall_trial = 1
        for i in range(len(sd)): #add subject field to each dict
            sd[i]['subject'] = f.split('/')[-1].split('.')[0]
            
            if(not "type" in sd[i].keys()):
                sd[i]["type"] = "TEXT"

            #print(sd[i])
            if(sd[i]["type"] == 'STUDY'):
                sd[i]["block"] = block
                sd[i]["trial"] = study_trial

                study_trial += 1

            if(sd[i]["type"] == 'RECALL'):
                sd[i]["trial"] = recall_trial
                sd[i]["block"] = block

                recall_trial += 1

            if(sd[i]['trial_type'] == 'instructions' and study_trial >= 14 and recall_trial >= 14):
                sd[i]["block"] = block
                study_trial = 1
                recall_trial = 1
                block += 1

                if(block > 5):
                    block = 1

                
            if 'face' in sd[i].keys():
                sd[i]['face'] = sd[i]['face'].split('/')[-1]
                sd[i]['faceidx'] = myfaces.index(sd[i]['face'])
                
                # TODO: should be neighbors within list, , not in facepool
                sd[i]['numneighbors'] = -1
                
            if 'responses' in sd[i].keys():
                sd[i]['possible_intrusions'] = np.zeros((len(bins)-1,))
                sd[i]['intrusion'] = np.nan
                sd[i]['distance'] = np.nan
                sd[i]['distance_bin'] = np.nan
                if sd[i]['type']=='MMFR': #handle MMFR trials specially
                    sd[i]['responses'] = [sd[i]['responses'].split('"')[3].upper(),
                                        sd[i]['responses'].split('"')[-2].upper()]
                else:
                    sd[i]['responses'] = sd[i]['responses'].split('"')[-2].upper()
                    
            if 'name' in sd[i].keys():
                if sd[i]['type']=='MMFR': #handle MMFR trials specially
                    sd[i]['name'][0] = sd[i]['name'][0].upper()
                    sd[i]['name'][1] = sd[i]['name'][1].upper()
                else:
                    sd[i]['name'] = sd[i]['name'].upper()
                    
        #add to growing list of subject data    
        sub_data.extend(sd)

    #Convert to dataframe and recarray
    df = pd.DataFrame(sub_data)
    recdat = df.to_records()

    #Calculate intrusions
    subs = np.unique(recdat['subject'])


    for s in subs:
        sub_evs = recdat[(recdat['subject']==s)]
        possible_names = set()
        for i in range(0, len(sub_evs)):
            if sub_evs[i]['type']=='STUDY':
                possible_names.add(sub_evs[i]["name"])
                
            if sub_evs[i]['type']=='RECALL':
                if sub_evs[i]['responses'] in possible_names and sub_evs[i]['responses'] != sub_evs[i]['name']:
                    #we have an intrusion! 
                    sub_evs[i]['intrusion'] = 1

                    #look up distance to intruded face
                    intr_name = sub_evs[i]['responses']
                    intr_face = sub_evs[(sub_evs['type']=='STUDY') & (sub_evs['name']==intr_name)]['face'][0]

                    true_face = sub_evs[i]['face']

                    #Indexed true, intrusion face
                    sub_evs[i]['distance'] = mds[myfaces.index(true_face), myfaces.index(intr_face)]
                    sub_evs[i]['possible_intrusions'], _ = np.histogram(mds[myfaces.index(true_face)], bins)
                    sub_evs[i]['numneighbors'] = np.sum(mds[myfaces.index(true_face)] < thresh)

                    dbin = np.digitize(sub_evs[i]['distance'], bins)
                    sub_evs[i]['distance_bin'] = dbin
                    
                elif not sub_evs[i]['responses'] in possible_names:
                    sub_evs[i]['intrusion'] = -1
                    sub_evs[i]['distance'] = -1
                    sub_evs[i]['distance_bin'] = -1
                    
                    true_face = sub_evs[i]['face']
                    sub_evs[i]['possible_intrusions'], _ = np.histogram(mds[myfaces.index(true_face)], bins)
                    sub_evs[i]['numneighbors'] = np.sum(mds[myfaces.index(true_face)] < thresh)
                    
                else:
                    sub_evs[i]['intrusion'] = 0

                    #look up distance to intruded face
                    intr_name = sub_evs[i]['responses']
                    intr_face = sub_evs[(sub_evs['type']=='STUDY') & \
                                                    (sub_evs['name']==intr_name)]['face'][0]
                    true_face = sub_evs[i]['face']

                    sub_evs[i]['distance'] = mds[myfaces.index(true_face), myfaces.index(intr_face)]
                    sub_evs[i]['possible_intrusions'], _ = np.histogram(mds[myfaces.index(true_face)], bins)
                    sub_evs[i]['numneighbors'] = np.sum(mds[myfaces.index(true_face)] < thresh)
                    #Indexed true, intrusion face
                    sub_evs[i]['distance'] = 0
                    sub_evs[i]['distance_bin'] = 0
                        
            recdat[(recdat['subject']==s)] = sub_evs
