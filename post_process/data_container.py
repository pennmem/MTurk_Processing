import pandas as pd
import json
import os
from functools import cached_property
from glob import glob


class DataContainer():
    def __init__(self, root='/', experiment='', survey="survey_responses.csv", db='', dictionary='dictionary.txt', wordpool='wordpool.txt'):
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
        with open(os.path.join(self.root, self._dictionary), "r") as f:
            return [w.strip().upper() for w in f.readlines()]

    @cached_property
    def wordpool(self):
        with open(os.path.join(self.root, self.experiment, self._wordpool), "r") as f:
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

    def get_raw_data(self, subjects=None):
        if not subjects == None \
           and not isinstance(subjects, list) \
           and not isinstance(subjects, tuple):
            subjects = [subjects]

        files = self.get_session_logs()

        if not subjects == None:
            files = self.filter_files_by_subject(files, subjects)

        return (self.read_session_log(f)["datastring"] for f in files)

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
        base_path = self.cleaned if cleaned else self.raw
        return glob(os.path.join(base_path, "*.json"))

    def get_subject_codes(self, cleaned=False):
        return [os.path.basename(f).split('.')[0] for f in self.get_session_logs(cleaned=cleaned)]


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

        return list(set(exc) | set(notes))
