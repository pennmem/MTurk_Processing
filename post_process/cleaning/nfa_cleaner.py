from experiment_cleaning import DataCleaner
from utils import progress_bar, strip_tags, change_key, filter_keys
import pandas as pd
import numpy as np

class NFACleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)
        self.event_types = [self.get_internal_events,
                            self.get_encoding_events, 
                            self.get_recall_events]

        self.modifiers = [self.add_list,
                          self.add_serialpos,
                          self.add_recalled]
                          

    def get_encoding_events(self, raw_data):
        data = raw_data["data"]
        events = []
        wanted_keys = ["block", "phase", "name"]

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "encoding":
                event = {}

                event = {k: trialdata[k] for k in wanted_keys}

                event["mstime"] = trialdata["time_elapsed"]
                event["type"] = "WORD"
                
                # TODO:
                event["face"] = trialdata['face'].split('/')[-1] 

                event["itemno"] = self.get_item_id(event["item"])
                

                events.append(event)

            return events

    def get_recall_events(self, raw_data):
        '''
        Break nodes of type free-recall into recall events with timestamps

        TODO: this method is largely repeated and should really have the bulk of the functionality
               inherited
        '''
        
        data = raw_data["data"]
        events = []
        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("trial_type", None) == "free-recall":
                recwords = trialdata["recwords"] 
                rts = trialdata["rt"]
                time = trialdata["start_time"]

                if len(recwords) == 0:
                    rts = [0]
                    recwords = [""]

                for w, t in zip(recwords, rts):
                    event = {}

                    event["mstime"] = time + t
                    event["rt"] = t

                    event["type"] = "REC_WORD"
                    event["item"] = w.upper() 
                    event["itemno"] = self.get_item_id(w.upper())
                    event["how"] = trialdata["conditions"]["how"]
                    event["when"] = trialdata["conditions"]["when"]

                    events.append(event)

        return events
