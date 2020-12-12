import pandas as pd
import json
import os
from functools import cached_property
from glob import glob


class DataContainer():
    def __init__(self, root='/', experiment='', survey='', db='', dictionary='', wordpool=''):
        self.root = root
        self.experiment = experiment
        self.db = db
        self.survey = survey
        self._dictionary = dictionary
        self._wordpool = wordpool

    @property
    def raw(self):
        return os.path.join(self.root, "raw")

    @property
    def cleaned(self):
        return os.path.join(self.root, "cleaned")

    @property
    def reports(self):
        return os.path.join(self.root, "reports")

    @cached_property
    def dictionary(self):
        with open(self._dictionary, "r") as f:
            return [w.strip().upper() for w in f.readlines()]

    @cached_property
    def wordpool(self):
        with open(self._wordpool, "r") as f:
            return [w.strip().upper() for w in f.readlines()]

    @staticmethod
    def read_session_log(file):
        with open(file, 'r') as f:
            raw = json.load(f)

        raw["datastring"] = json.loads(raw["datastring"])
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

    def cleaned(self, sub):
        return os.path.exists(self.path_from_code(sub, cleaned=True))
        
    def get_raw_data(self, subjects=None):
        if not subjects == None \
           and not isinstance(subjects, list) \
           and not isinstance(subjects, tuple):
            subjects = [subjects]

        files = self.get_session_logs()

        if not subjects == None:
            files = self.filter_files_by_subject(files, subjects)

        return [self.read_session_log(f)["datastring"] for f in files] 

    def get_cleaned_data(self, subjects=None):
        # TODO: catch error to note whether not cleaned data is available
        # want specific Exception class for this

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

    def get_session_logs(self, cleaned=False):
        if not cleaned:
            return [os.path.join(self.raw, f'{code}.json') for code in self.get_subject_codes(cleaned=cleaned)]
        else:
            return [os.path.join(self.cleaned, f'{code}.json') for code in self.get_subject_codes(cleaned=cleaned)]


    def get_subject_codes(self, cleaned=False):
        base_path = self.cleaned if cleaned else self.raw
        return [os.path.basename(f).split('.')[0] for f in glob(os.path.join(base_path, "*.json"))]


    # TODO: these functions are clunky (moreso than all the other clunky things)
    # would be nice to streamline management of these things (func with file to write as param?)
    def record_excluded(self, subjects: list):
        EXCLUDED = os.path.join(self.root, 'EXCLUDED.txt')

        if os.path.exists(EXCLUDED):
            with open(EXCLUDED, 'r') as f:
                exc = [s.strip() for s in f.readlines()]

            exc = list(set(exc) | set(subjects))
        else:
            exc = subjects

        with open(EXCLUDED, 'w') as f:
            f.write("\n".join(exc))

    def record_wrote_notes(self, subjects: list):
        WROTE_NOTES = os.path.join(self.root, 'WROTE_NOTES.txt')

        if os.path.exists(WROTE_NOTES):
            with open(WROTE_NOTES, 'r') as f:
                wn = [s.strip() for s in f.readlines()]

            wn = list(set(wn) | set(subjects))
        else:
            wn = subjects

        with open(WROTE_NOTES, 'w') as f:
            f.write("\n".join(wn))

    def save_df(self, df, subject):
        df.to_json(self.path_from_code(subject, cleaned=True))

    def get_bad_subs(self):
        EXCLUDED = os.path.join(self.root, 'EXCLUDED.txt')
        WROTE_NOTES = os.path.join(self.root, 'WROTE_NOTES.txt')

        with open(EXCLUDED, 'r') as f:
            exc = [s.strip() for s in f.readlines()]

        with open(WROTE_NOTES, 'r') as f:
            notes = [s.strip() for s in f.readlines()]

        return exc + notes
