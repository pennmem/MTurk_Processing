from post_process.cleaning.experiment_cleaning import DataCleaner 
from post_process.utils import progress_bar, strip_tags, change_key, filter_keys
import pandas as pd
import numpy as np

class PresRateCleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)

        self.event_types = [self.get_internal_events,
                            self.get_encoding_events,
                            self.get_math_distractor_events,
                            self.get_recall_events]

        self.modifiers = [self.add_list,
                          self.add_serialpos,
                          self.correct_recalls,
                          self.add_recalled,
                          self.add_intrusion]


    def get_encoding_events(self, raw_data):
        data = raw_data["data"]
        events = []
        wanted_keys = ["block", "length", "pr"]

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "encoding" \
                or trialdata.get("type", None) == "practice":
                event = {}

                event = filter_keys(wanted_keys, trialdata)

                event["mstime"] = trialdata["time_elapsed"]
                event["type"] = "WORD"
                event["item"] = strip_tags(trialdata["stimulus"])
                event["itemno"] = self.get_item_id(event["item"])

                events.append(event)

        return events


    def get_recall_events_hack(self, raw_data):
        '''
        Break nodes of type free-recall into recall events with timestamps
        '''

        data = raw_data["data"]
        events = []
        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("trial_type", None) == "free-recall":
                recwords = trialdata["recwords"] 
                rts = trialdata["rt"]

                if len(recwords) == 0:
                    rts = [0]
                    recwords = [""]

                for w, t in zip(recwords, rts):
                    event = {}

                    # hack using hardcoded experiment times
                    # from task design. If this is going to be
                    # an approach in the future, we need a way
                    # to get the experiment information into this pipeline
                    if "mstime" in event:
                        event["mstime"] = trialdata["time_elapsed"] - 75000 + t 

                    event["rt"] = t
                    event["type"] = "REC_WORD"
                    event["item"] = w.upper() 
                    event["itemno"] = self.get_item_id(w.upper())

                    events.append(event)

        return events
