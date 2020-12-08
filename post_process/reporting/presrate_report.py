from glob import glob
import pandas as pd
import json
import os


# TODO: make this maintainable, cleaner
# TODO: create recall matrices as step 1
def presrate_report(paths_dict):
    """
    Given paths for a given experiment, write out reports and summary statistics for each participant
    as well as summaries across subjects

    :param paths_dict: dictionary describing layout of data, event, stats, and reports directories for given experiment
    :return: 
    """

    files = glob(os.path.join(paths_dict["data"],'MTK*.json'))

    #Load subject data from json files
    sub_data = []

    for f in files:
        listnum = 0 # for keeping track of lists
        # sd = json.load(open(f));
        sd = pd.read_json(f); 
        print(sd)
        return

        
        for i in range(0, len(sd)): 
            #Don't need any other trial types for now
            if str(sd[i]['trial_type']) != 'free-recall' and str(sd[i]['trial_type']) != 'html-keyboard-response':
                continue

            sd[i]['subject'] = f.split('.')[-2].split('/')[-1] #add subject field to each dict
            sd[i]['list_length'] = np.nan
            sd[i]['presentation_rate'] = np.nan
            
            #Get serial position
            if str(sd[i]['trial_type'])=='html-keyboard-response':
                serial_pos = int(float(sd[i]['internal_node_id'].split('-')[-1]))
                sd[i]['serial_pos'] = serial_pos        

            #See if this is a new list
            if serial_pos == 0:
                newlist=True
            else:
                newlist=False
            
            #Advance list counter if new list
            if newlist:
                listnum += 1
            
            #Add list ID to each item
            sd[i]['list'] = listnum
                
            if str(sd[i]['trial_type']) == 'free-recall': #Only engage for response trials
                sub_data.append(sd[i])
                
                words = [str(w.upper()) for w in sd[i]['recwords']]
                
                #See whether there's matches for all of the prior data in the current list
                for j in range(0, len(sd)):
                    if j<i:
                        
                        #Don't need any other trial types
                        if str(sd[j]['trial_type']) != 'free-recall' and str(sd[j]['trial_type']) != 'html-keyboard-response':
                            continue
                            
                        if sd[j]['subject'] == sd[i]['subject'] and sd[j]['list'] == sd[i]['list']: #check for true recalls
                            if str(sd[j]['stimulus'].split('<')[-2].split('>')[-1]) in words:
                                sd[j]['recalled']=1
                            else:
                                sd[j]['recalled']=0
                        else:
                            continue
                    else:
                        break
                    
            #add to growing list of subject data
            if str(sd[i]['trial_type'])=='html-keyboard-response':
                sub_data.append(sd[i])
                        
    #Convert to dataframe and recarray
    df = pd.DataFrame(sub_data)
    df = df[df["list"] != 1]
    recdat = df.to_records()

    #Now go back through and label long/short list, long/short presentation
    unique_subs = np.unique(recdat['subject'])

    for s in unique_subs:
        idxs = np.where(recdat['subject']==s)
        unique_lists = np.unique(recdat[idxs]['list'])
        for l in unique_lists:
            list_idxs = np.where(np.logical_and(recdat['list']==l, recdat['subject']==s))
            if np.sum((recdat[list_idxs]['list'] == l) & (recdat[list_idxs]['trial_type'] == 'html-keyboard-response') ) > 12:
                for i in list_idxs[0]:
                    recdat[i]['list_length'] = 1
            else:
                for i in list_idxs[0]:
                    recdat[i]['list_length'] = 0

            pr = recdat[list_idxs][1]['time_elapsed']-recdat[list_idxs][0]['time_elapsed']
            if pr > 1800:
                for i in list_idxs[0]:
                    recdat[i]['presentation_rate'] = 1
            else:
                for i in list_idxs[0]:
                    recdat[i]['presentation_rate'] = 0 

        print("Processed {}".format(s))
