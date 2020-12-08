import traceback as tb
import pandas as pd
import numpy as np
import json
import csv
import os
from pyxdameraulevenshtein import damerau_levenshtein_distance_ndarray
from post_process.utils import progress_bar, strip_tags, change_key, filter_keys

from post_process.cleaning.plugin_processing import  html_keyboard_response_node, hold_keys_node, \
                               hold_keys_check_node, free_recall_node, \
                               free_sort_node, positional_html_display_node, \
                               math_distractor_node, countdown_node

class DataCleaner(object):
    def __init__(self, data_container):
        self.data_container = data_container 

        self.modifiers = []
        self.event_types = []



    @progress_bar()
    def clean(self, force=False, verbose=False):

        self.process_survey()

        raw_data_all_subs = self.data_container.get_raw_data()

        total = len(raw_data_all_subs)

        print("Cleaning subject data")

        errors = []
        exclude = []

        for i, raw_data in enumerate(raw_data_all_subs):

            # progress bar decorator expects function to generate a fraction of its total
            yield (i/total)

            events_list = []
            subject = self.get_subject(raw_data)

            if self.data_container.cleaned(subject) and not force:
                continue

            try:
                for ev_type in self.event_types:
                    events_list.append(ev_type(raw_data))

                events_df = pd.concat(events_list, sort=True)
                events_df["subject"] = self.get_subject(raw_data)
                events_df["condition"] = self.get_condition(raw_data)
                events_df["counterbalance"] = self.get_counterbalance(raw_data)

                del events_list

                for modifier in self.modifiers:
                    events_df = modifier(events_df)

                # saving
                events_df = events_df.reset_index()
                self.data_container.save_df(events_df, subject)

                if(self.exclude_subject(events_df)):
                    exclude.append(subject)

            except Exception:
                # TODO: add verbose arg
                if verbose:
                    tb.print_exc()
                errors.append(subject)

        yield 1.0

        # errors are recorded in .txt files so that 
        # database access is not needed to work with data.
        # In principle, the database contains PHI and should
        # not be open to all analysts
        self.data_container.record_excluded(exclude)
        
        if verbose:
            print(errors)

        # progress bar can optionally return a final result
        return None 

    ####################
    # Collection of functions that extract pieces of common format from jspsych 
    ####################


    # TODO: should these be data_container functions?
    # at the moment, this class seems to hold both the base class
    # and the implementation for jspsych, when much of this
    # could also be used for other lab data otherwise
    def get_item_id(self, item):
        if item not in self.data_container.wordpool:
            return -1

        return self.data_container.wordpool.index(item)

    def get_subject(self, raw_data):
        return raw_data['workerId']

    def get_starttime(self, raw_data):
        # TODO: logging a start time to the experiment would be much more effective
        return raw_data["data"][0]["dateTime"] - raw_data["data"][0]["trialdata"]["time_elapsed"]

    def get_trialdata(self, raw_data):
        return [record['trialdata'] for record in self.get_data(raw_data)]

    def get_data(self, raw_data):
        return raw_data['data']

    def get_questionnaire(self, raw_data):
        return raw_data["questiondata"] 

    def get_condition(self, raw_data):
        return raw_data["condition"]

    def get_counterbalance(self, raw_data):
        return raw_data["counterbalance"]

    def get_version(self, raw_data):
        # TODO: this needs to be grabbed from metadata, as it's not in datastring
        raise NotImplementedError("Not yet implemented")

    def get_encoding_events(self, raw_data):
        raise NotImplementedError("Experiment specific")

    def get_orientation_events(self, raw_data):
        raise NotImplementedError("Experiment specific")

    def get_recall_events(self, raw_data):
        '''
        Break nodes of type free-recall into recall events with timestamps
        '''
        
        data = raw_data["data"]
        events = []
        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("trial_type", None) == "free-recall":
                events.extend(free_recall_node(trialdata))
        
        return pd.DataFrame(events)

    def get_math_distractor_events(self, raw_data):
        '''
        Break nodes of type math-distractor into individual events with timestamps
        dateTime -> mstime
        trialtype -> type
        '''

        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("trial_type", None) == "math-distractor":
               events.extend(math_distractor_node(trialdata)) 

        return pd.DataFrame(events)

    def get_internal_events(self, raw_data):
        '''
        eventtype -> type
        timestamp -> mstime
        value -> value
        interval -> interval
        '''
        events = raw_data['eventdata'] 
        events = [change_key("eventtype", "type", e) for e in events]
        events = [change_key("timestamp", "mstime", e) for e in events]

        wanted_keys = ["type", "mstime", "value", "interval"]
        events = [{k: e[k] for k in wanted_keys} for e in events]

        events = pd.DataFrame(events)

        # internal events are recorded as unixtime, task events are
        # recored by offset from task start
        events["mstime"] = events["mstime"] - self.get_starttime(raw_data)
        
        return events

    def get_countdown_events(self, raw_data):
        data = raw_data["data"]
        events = []


        for record in data:
            trialdata = record["trialdata"]
            if trialdata.get("trial_type", None) == "countdown":
               events.extend(countdown_node(trialdata)) 

        return pd.DataFrame(events)


    def process_survey(self):
        
        outfile = self.data_container.survey
        to_process = self.data_container.get_subject_codes(cleaned=False)

        # Load existing survey spreadsheet
        if os.path.exists(outfile):
            with open(outfile, 'r') as f:
                r = csv.reader(f, delimiter=',')

                # cuts off header
                s = [row for row in r][1:]

            already_processed = [row[0] for row in s]
            to_process = [code for code in to_process if code not in already_processed]

        for subj in to_process:
            data,  = self.data_container.get_raw_data(subj)
            cond = self.get_condition(data)

            try:
                data = self.get_questionnaire(data)
            except:
                # this subject didn't complete the questionnaire, which will
                # be picked up on elsewhere. As this structure is a little
                # clunky, this should be folded in with the iterative cleaning
                # and may be added to the ERRORS file
                continue

            # Extract demographic info
            age = data['age'] if 'age' in data else ''
            education = data['education'] if 'education' in data else 'Not Reported'
            ethnicity = data['ethnicity'] if 'ethnicity' in data else 'Not Reported'
            gender = data['gender'] if 'gender' in data else 'Not Reported'
            gender_other = data['gender_other'] if 'gender_other' in data else ''
            language = data['language'] if 'language' in data else 'Not Reported'
            marital = data['marital'] if 'marital' in data else 'Not Reported'
            origin = data['origin'] if 'origin' in data else 'Not Reported'
            race = '|'.join(data['race']) if 'race' in data else 'Not Reported'
            race_other = data['race_other'] if 'race_other' in data else ''

            strat_categorize = data['strat-categorize'] if 'strat-categorize' in data else ''
            strat_image = data['strat-image'] if 'strat-image' in data else ''
            strat_rehearsal = data['strat-rehearsal'] if 'strat-rehearsal' in data else ''
            strat_spatial = data['strat-spatial'] if 'strat-spatial' in data else ''
            strat_story = data['strat-story'] if 'strat-story' in data else ''

            strat_other = data['strat-other'] if 'strat-other' in data else ''

            if 'wrote-notes' in data:
                if data['wrote-notes'] == 'Yes':
                    wrote_notes = '1'
                elif data['wrote-notes'] == 'No':
                    wrote_notes = '0'
                else:
                    wrote_notes = ''
            else:
                wrote_notes = ''

            if 'distracted' in data:
                if data['distracted'] == 'Yes':
                    distracted = '1'
                elif data['distracted'] == 'No':
                    distracted = '0'
                else:
                    distracted = ''
            else:
                distracted = ''

            # Add new row to spreadsheet
            s.append([subj, age, education, ethnicity, gender, gender_other, language, marital, origin, race, race_other,
                    strat_categorize, strat_image, strat_rehearsal, strat_spatial, strat_story,
                    strat_other, wrote_notes, distracted])

        head = ['subject', 'age', 'education', 'ethnicity', 'gender', 'gender_other', 'language', 'marital', 'origin',
            'race', 'race_other', 'strat_categorize_aud', 'strat_categorize_vis', 'strat_image_aud',
            'strat_image_vis', 'strat_rehearsal_aud', 'strat_rehearsal_vis', 'strat_spatial_aud',
            'strat_spatial_vis', 'strat_story_aud', 'strat_story_vis', 'strat_other', 'wrote_notes', 'distracted']

        # Sort by subject ID
        s.sort(key=lambda x: x[0])

        # TODO: standardize on json

        # Write data out to file
        # TODO: rely on datacontainer for this
        with open(outfile, 'w') as f:
            w = csv.writer(f, delimiter=',')
            w.writerow(head)
            for row in s:
                w.writerow(row)

        print("Survey summary saved")

        # Write out WROTE_NOTES.txt file
        all_subj = np.array(s)[:, 0]
        wn = np.array(s)[:, -2]
        subj_wrote_notes = all_subj[wn == '1']
        self.data_container.record_wrote_notes(subj_wrote_notes)

        return {"data": s, "header": head}


    ####################
    # Functions that deal with derived data structures that adhere to the standard event specification
    ####################

    def add_itemno(self, events):
        events.loc[(events["type"] == 'WORD') | (events["type"] == 'REC_WORD'), "itemno"]  \
                = events.loc[(events["type"] == 'WORD') | (events["type"] == 'REC_WORD'),"item"] \
                        .apply(lambda x: self.get_item_id(x))

        return events

    def add_serialpos(self, events):
        '''
        Adds sequential index to WORD events on the same list.
        Requires list and itemnos fields to be populated.
        '''

        def find_presentation(row):
            try:
                return events.loc[(events["type"] == 'WORD') & (events["itemno"] == row["itemno"]) & (events["listno"] == row["listno"]), "serialpos"]
            except KeyError:
                return -1
            

        events = events.sort_values("mstime")
        events["temp"] = np.ones((len(events.index), ))
        events.loc[events["type"] == 'WORD', "serialpos"] = events.loc[events["type"] == 'WORD'].groupby("listno").cumsum()["temp"]
        events.loc[events["type"] == 'REC_WORD', "serialpos"] = events.loc[events["type"] == 'REC_WORD'].apply(find_presentation, axis=1)
        events = events.drop("temp", axis=1)

        return events


    def add_list(self, events):
        '''
        uses END_RECALL events to determine when a new list begins
        '''
        events = events.sort_values("mstime")

        # TODO: start list event
        end_rec = events["type"].values == "END_RECALL"
        new_list = np.pad(np.asarray(end_rec[1:] < end_rec[:-1]), ((1, 0), ), mode="constant" )
        list_vec = np.cumsum(new_list)
        events["listno"] = list_vec

        return events

    def add_intrusion(self, events):
        '''
        uses REC_WORD and WORD events to determine if a recalled word is a PLI/XLI
        '''
        events = events.sort_values("mstime")

        def check_list(row):
            
            presentation = events[(events["type"] == 'WORD') \
                                  & (events["itemno"] == row["itemno"]) \
                                  & (events["listno"] <= row["listno"])]

            if len(presentation.index) == 0:
                return -1
            else:
                # also captures repeated presentations
                list_delta = row["listno"] - presentation.iloc[-1]["listno"]
                # list_delta = list_delta.values[0] # Series are annoying

                return -1 if list_delta < 0 else list_delta


        events.loc[events["type"] == 'REC_WORD', "intrusion"] = events[events["type"] == 'REC_WORD'].apply(check_list, axis=1)

        return events

    def add_recalled(self, events):
        '''
        uses REC_WORD and WORD events to determine if a word is recalled.
        Requires list field to be populated.
        '''
        def find_recall(row):
            itemno = row["itemno"]
            recalls = events[(events["type"] == 'REC_WORD') & (events["listno"] == row["listno"])]["itemno"].values

            return itemno in recalls

        events = events.sort_values("mstime")

        events.loc[events["type"] =="WORD", "recalled"] = events.loc[events["type"] == "WORD"].apply(find_recall, axis=1)

        return events

    def add_recalled_serialpos(self, events):
        '''
        uses REC_WORD and WORD events to determine if a recalled word is a PLI/XLI
        '''
        events = events.sort_values("mstime")

        def check_list(row):
            
            presentation = events[(events["type"] == 'WORD') & (events["itemno"] == row["itemno"]) & (events["listno"] == row["listno"])]

            if len(presentation.index) == 0:
                return -1
            else:
                # captures first presentation for repeats
                return presentation["serialpos"].values[0] # series are annoying

        events.loc[events["type"] == 'REC_WORD', "serialpos"] = events[events["type"] == 'REC_WORD'].apply(check_list, axis=1)

        return events

    def add_list_length(self, events):
        for l in events.listno.unique():
            events.loc[events["listno"] == l, "list_length"] = len(events.loc[(events["type"] == 'WORD') & (events["listno"] == l)].index)

        return events

    def add_repeats(self, events):
        raise NotImplementedError();

    # breaking from naming for descriptiveness
    def expand_conditions(self, events):
        return pd.concat([events.drop(['conditions'], axis=1), events['conditions'].apply(pd.Series)], axis=1)

    def correct_recalls(self, events):
        '''
        spellcheck recalls and update item and itemno fields
        '''

        def apply_correction(row):
            item = row["item"]

            presented = events[(events["listno"] <= row["listno"]) & (events["type"] == 'WORD')]["item"].values

            ret = self._correct_spelling(item, presented)
            return ret

        # apply correction to every word event
        events.loc[events["type"] == "REC_WORD", "item"] = events[events["type"] == "REC_WORD"].apply(apply_correction, axis=1)

        # search for word num on all events
        events.loc[events["type"] == "REC_WORD", "itemno"] = events[events["type"] == "REC_WORD"].apply(lambda x: self.get_item_id(x["item"]), axis=1)

        # add recalled to all word events
        events = self.add_recalled(events)

        return events

    ####################
    # Functions to generate additional derived files from data
    ####################     

    # TODO: lost focus filter
    # TODO: math filter
    def exclude_subject(self, events, recall_thresh=.95, no_recalls_thresh=1):
        recalls_by_list = events[(events["type"] == 'WORD')].groupby("listno")["recalled"].sum()
        presentations = len(events[(events["type"] == 'WORD')].index)
        all_recalls = np.sum(recalls_by_list)

        if all_recalls >= presentations * recall_thresh:
            return True 

        no_recall_lists = np.sum(recalls_by_list.values == 0)
        if no_recall_lists > no_recalls_thresh:
            return True

        return False

    def _correct_spelling(self, recall, presented):
        # short circuit if correct
        if recall in presented:
            return recall

        # edit distance to each item in the pool and dictionary
        dist_to_pool = damerau_levenshtein_distance_ndarray(recall, np.asarray(presented))
        dist_to_dict = damerau_levenshtein_distance_ndarray(recall, np.asarray(self.data_container.dictionary))
    
        # position in distribution of dist_to_dict
        ptile = np.true_divide(sum(dist_to_dict <= np.amin(dist_to_pool)), dist_to_dict.size)
    
        # decide if it is a word in the pool or an ELI
        if ptile <= .1:
            return presented[np.argmin(dist_to_pool)]
        else:
            return self.data_container.dictionary[np.argmin(dist_to_dict)]
