from post_process.cleaning.experiment_cleaning import DataCleaner, EventDecorators 
from post_process.cleaning.plugin_processing import hold_keys_node
import pandas as pd
import numpy as np

class RepFRCleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)

        self.event_types = [self.get_internal_events,
                self.get_encoding_events, 
                self.get_recall_events,
                self.get_rest_events,
                self.get_countdown_events]

        self.modifiers = [self.add_itemno,
                self.add_list,
                self.add_list_length,
                self.expand_conditions,
                self.correct_recalls,
                self.add_serialpos,
                self.add_repeats,
                self.add_recalled,
                self.add_recalled_serialpos,
                self.add_intrusion]

    def get_encoding_events(self, raw_data):
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "encoding":
                node_events = hold_keys_node(trialdata)
                events.extend(node_events)

        return events
    

    def get_rest_events(self, raw_data):
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("trial_type", None) == "hold-keys" \
                    and trialdata.get("type", None) == 'fixation':
                    node_data = hold_keys_node(trialdata)
                    node_data["type"] = "REST"
                    events.extend(node_data)

        return events

    def add_repeats(self, events):

        repeat_mask = events.duplicated(subset=["type", "itemno"])

        events.loc[repeat_mask, "is_repeat"] = True
        events.loc[~repeat_mask, "is_repeat"] = False
        # events.loc[events["type"] == 'WORD', "repeat"] = 

        # FIXME: this could be a lot more readable
        for itemno in events[events["type"] == "WORD"]["itemno"].unique():
            events.loc[((events["type"] == "WORD") | (events["type"] == "REC_WORD")) & (events["itemno"] == itemno), "repeats"] = len(events[(events["itemno"] == itemno) & (events["type"] == "WORD")])

        return events
