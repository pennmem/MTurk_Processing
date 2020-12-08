import os
import json
import numpy as np
import pandas as pd
from glob import glob
from write_to_json import write_data_to_json
from sqlalchemy import create_engine, MetaData, Table
# from pyxdameraulevenshtein import damerau_levenshtein_distance_ndarray


def load_psiturk_data(db_url, table_name, paths_dict, data_column_name='datastring', force=False):
    """
    Extracts the data from each participant in a psiTurk study, then writes as a JSON file for each participant.

    :param db_url: The location of the database as a string. If using mySQL, must include username and password, e.g.
    'mysql://user:password@127.0.0.1:3306/mturk_db'
    :param table_name: The name of the experiment's table within the database, e.g. 'ltpFR3'
    :param event_dir: The path to the directory where raw event data will be written into JSON files.
    :param data_column_name: The name of the column in which psiTurk has stored the actual experiment event data. By
    default, psiTurk labels this column as 'datastring'
    :param force: If False, only write JSON files for participants that don't already have a JSON file. If True, create
    JSON files for all participants. (Default == False)
    """

    """
    Status codes are as follows:
    NOT_ACCEPTED = 0
    ALLOCATED = 1
    STARTED = 2
    COMPLETED = 3
    SUBMITTED = 4
    CREDITED = 5
    QUITEARLY = 6
    BONUSED = 7
    """
    complete_statuses = [3, 4, 5, 7]  # Status codes of subjects who have completed the study

    # Use sqlalchemy to load rows from specified table in the specified database
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.bind = engine
    table = Table(table_name, metadata, autoload=True)
    s = table.select()
    rows = s.execute()

    for row in rows:
        # Get subject ID
        subj_id = row['workerid']
        datafile_path = os.path.join(paths_dict["event"], '%s.json' % subj_id)
        inc_datafile_path = os.path.join(paths_dict["event"], 'incomplete', '%s.json' % subj_id)

        # Extract participant's data string
        data = row[data_column_name]

        # Only attempt to write a JSON file if the participant has data and does not already have a JSON file
        if data != '' and not os.path.exists(datafile_path):
            # Parse data string as a JSON object
            try:
                data = json.loads(data)
            except:
                print('Failed to parse session log for %s as a JSON object! Skipping...' % subj_id)
                continue

            # Write JSON data to a file if the file does not already exist
            if force or not os.path.exists(datafile_path):
                with open(datafile_path, 'w') as f:
                    json.dump(data, f)

        # Move logs from incomplete sessions to their own folder
        status = row['status']
        if status not in complete_statuses and os.path.exists(datafile_path):
            os.rename(datafile_path, inc_datafile_path)
        # Remove logs previously marked as incomplete if they have now become complete
        elif status in complete_statuses and os.path.exists(inc_datafile_path):
            os.remove(inc_datafile_path)


def process_psiturk_data(paths_dict , webster_path, force=False):
    """
    Post-process the raw psiTurk data extracted by load_psiturk_data. This involves creating recalls and presentation
    matrices, extracting list conditions, etc. The matrices created are saved to a JSON file for each participant.

    :param paths_dict: A dictionary containing the paths where data is stored for this experiment, expects "event", "data", and 
    :param webster_path: The path to the text file containing the English dictionary to use for spell-checking.
    :param force: If False, only process data from participants who do not already have a behavioral matrix file. If
    True, process data from all participants. (Default == False)
    """

    data_root = paths_dict["root"]
    behmat_dir = paths_dict["data"]
    event_dir = paths_dict["event"]

    # Load the English dictionary file, remove spaces, and make all words lowercase
    with open(webster_path, 'r') as df:
        dictionary = df.readlines()
    dictionary = [word.lower().strip() for word in dictionary if ' ' not in word]

    # Load list of excluded participants
    exclude = [s.decode('UTF-8') for s in np.loadtxt(os.path.join(data_root, 'EXCLUDED.txt'), dtype='S8')]
    bad_sess = [s.decode('UTF-8') for s in np.loadtxt(os.path.join(data_root, 'BAD_SESS.txt'), dtype='S8')]
    rejected = [s.decode('UTF-8') for s in np.loadtxt(os.path.join(data_root, 'REJECTED.txt'), dtype='S8')]

    # Process each participant's raw data into a JSON file of behavioral matrices
    for json_file in glob(os.path.join(event_dir, '*.json')):

        s = os.path.splitext(os.path.basename(json_file))[0]  # Get subject ID from file name
        outfile = os.path.join(behmat_dir, '%s.json' % s)  # Define file path for behavioral matrix file
        # Skip bad sessions and participants who have already been processed, excluded, or rejected
        if s in bad_sess or ((os.path.exists(outfile) or s in exclude or s in rejected) and not force):
            continue
        
        data = _read_raw_json([json_file])
        print(s)
        # write_data_to_json(data, outfile)
        data.to_json(outfile)


def _read_raw_json(files):
    all_data = []
    for f in files:
        with open(json_file, 'r') as f:
            data = json.load(f)
        s = data['workerId']
        
        sub_data = []
        for record in data["data"]:
            record = record['trialdata']
            record["subject"] = s
            sub_data.append(record)
            
        all_data.append(pd.DataFrame(sub_data))
      
    return pd.concat(all_data)

