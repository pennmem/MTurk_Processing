import pandas as pd
import json
import os
from functools import cached_property, reduce
from glob import glob
import importlib.resources as pkg_resources
import post_process.resources as resources


class DataContainer():
    ''' Class that wraps file io and management of experiment files. This doesn't retain
    any information about the internal format of said files aside from their being
    json files. Users of this class will receive data as a dictionary if reading
    raw data or as a dataframe for cleaned data, and must validate the internal format
    themselves.
    '''

    def __init__(self, root='/', experiment='', survey="survey_responses.csv", db='', dictionary=None, wordpool=None):
        self.root = root
        self.experiment = experiment
        self.db = db
        self._survey = survey
        self._dictionary = dictionary
        self._wordpool = wordpool

    @property
    def raw(self):
        return os.path.join(self.root, self.experiment, "raw")

    @property
    def cleaned(self):
        return os.path.join(self.root, self.experiment, "cleaned")

    @property
    def reports(self):
        return os.path.join(self.root, self.experiment, "reports")

    @property
    def survey(self):
        return os.path.join(self.root, self.experiment, self._survey)

    @cached_property
    def dictionary(self):
        if self._dictionary:
            with open(os.path.join(self.root, self._dictionary), "r") as f:
                return [w.strip().upper() for w in f.readlines()]
        else:
            return [w.strip().upper() for w in pkg_resources.read_text(resources, 'webster_dictionary.txt').split()]

    @cached_property
    def wordpool(self):
        if self._wordpool:
            with open(os.path.join(self.root, self.experiment, self._wordpool), "r") as f:
                return [w.strip().upper() for w in f.readlines()]
        else:
            return [w.strip().upper() for w in pkg_resources.read_text(resources, 'wordpool.txt').split()]

    @staticmethod
    def read_session_log(file):
        with open(file, 'r') as f:
            raw = json.load(f)

        for key in raw.keys():
            # server responses may be sent as
            # json parsed as a string

            try:
                raw[key] = json.loads(raw[key])
            except ValueError:
                continue

        return raw

    def filter_files_by_subject(self, files, subjects):
        files = [f for f in files if self.code_from_path(f) in subjects]

        if files == []:
            raise Exception("No files for given subjects")

        if len(files) != len(subjects):
            raise Exception("Files do not match subjects")

        return files

    def code_from_path(self, path):
        return os.path.basename(path).split(".")[0]

    def path_from_code(self, code, cleaned=False):
        if cleaned:
            return os.path.join(self.cleaned, f"{code}.json")
        else:
            return os.path.join(self.raw, f"{code}.json")

    def get_subject_codes(self, cleaned=False):
        return [self.code_from_path(f) for f in self.get_session_logs(cleaned=cleaned)]

    def get_session_logs(self, cleaned=False):
        base_path = self.cleaned if cleaned else self.raw
        return glob(os.path.join(base_path, "*.json"))

    def get_raw_data(self, subjects=None):
        if not subjects == None \
           and not isinstance(subjects, list) \
           and not isinstance(subjects, tuple):
            subjects = [subjects]

        files = self.get_session_logs(cleaned=False)

        if not subjects == None:
            files = self.filter_files_by_subject(files, subjects)

        return [self.read_session_log(f) for f in files]

    def get_cleaned_data(self, subjects=None):
        # TODO: catch error to note whether not cleaned data is available

        if not subjects is None \
           and not isinstance(subjects, list) \
           and not isinstance(subjects, tuple):
            subjects = [subjects]

        files = self.get_session_logs(cleaned=True)

        if not subjects is None:
            files = self.filter_files_by_subject(files, subjects)
        else:
            files = [f for f in files if os.path.basename(f).split('.')[0] not in self.get_bad_subs()]

        all_data = []
        for f in files:
            with open(f, 'r') as f:
                all_data.append(pd.read_json(f))
        
        return pd.concat(all_data) 

    def record_collection(self, subjects: list, fname: str):
        path = os.path.join(self.root, self.experiment, f"{fname}.txt")
        subjects = set(subjects)

        if os.path.exists(path):
            with open(path, 'r') as f:
                exists = set(s.strip() for s in f.readlines())

            union = list(exists | subjects)
        else:
            union = subjects

        with open(path, 'w') as f:
            f.write("\n".join(union))

    def record_excluded(self, subjects: list):
        self.record_collection(subjects, "EXCLUDED")

    def record_wrote_notes(self, subjects: list):
        self.record_collection(subjects, "WROTE_NOTES")

    def read_collection(self, fname: str):
        path = os.path.join(self.root, self.experiment, f"{fname}.txt")
        if os.path.exists(path):
            with open(path, 'r') as f:
                subs = set(s.strip() for s in f.readlines())
            return subs
        else:
            return set()

    def save_df(self, df, subject):
        df.to_json(self.path_from_code(subject, cleaned=True))

    def get_bad_subs(self, bad_collections: list = ["EXCLUDED", "WROTE_NOTES"]):
        return reduce(lambda a, b: a | b, map(self.read_collection, bad_collections))
