import os
import json
import numpy as np
import pandas as pd
from glob import glob
# FIXME
from worker_management import DBManager

def anonymize_row(row, workerid, anonymousid):
    # remove ip
    row.ip = "XX.XXX.XXX.XX"
    row.workerid = anonymousid
    row.uniqueid = row.uniqueid.replace(workerid, anonymousid)
    row.datastring = row.datastring.replace(workerid, anonymousid)

    return row


def load_psiturk_data(data_container, force=False, verbose=False):
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

    # Use sqlalchemy to load rows from specified table in the specified database
    with DBManager(data_container.db) as db:
        if not data_container.class_exp:
            db.add_workers_from_experiment(data_container.experiment)
        complete_subs = db.get_complete_subjects(data_container.experiment, class_exp=data_container.class_exp)

    for row in complete_subs:

        if not data_container.class_exp:
            # Get subject ID
            with DBManager(data_container.db) as db:
                subj_id = db.get_anonymous_id(row.workerid)

            row = anonymize_row(row, row.workerid, subj_id)
        datafile_path = data_container.path_from_code(subj_id)

        # Only attempt to write a JSON file if the participant has data and does not already have a JSON file
        if force or not os.path.exists(datafile_path):
            with open(datafile_path, 'w') as f:
                json.dump(row.as_dict(), f)

def _read_raw_json(files):
    all_data = []
    for json_file in files:
        with open(json_file, 'r') as f:
            data = json.load(f)
        s = data['workerid']
        
        sub_data = []
        for record in data["data"]:
            record = record['trialdata']
            record["subject"] = s
            sub_data.append(record)
            
        all_data.append(pd.DataFrame(sub_data))
      
    return pd.concat(all_data)
