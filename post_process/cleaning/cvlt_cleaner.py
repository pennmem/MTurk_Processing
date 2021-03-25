from post_process.cleaning.experiment_cleaning import DataCleaner
from post_process.utils import progress_bar, strip_tags, change_key, filter_keys
from post_process.cleaning.plugin_processing import  html_keyboard_response_node, free_recall_node, audio_keyboard_response_node
import pandas as pd
import numpy as np


class CVLTCleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)

        self.event_types = [self.get_internal_events,
                            self.get_encoding_events, 
                            self.get_recall_events,
                            self.get_math_distractor_events,
                            ]

        self.modifiers = [self.add_itemno,
                          self.add_list,
                          self.add_serialpos,
                          self.add_recalled,
                          self.add_intrusion,
                          self.add_recalled_serialpos]

    def get_recall_events(self, raw_data):
        # entirely different from normal recall, deals with both final recall and repositioning
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("type", None) == "recall":
                node_events = free_recall_node(trialdata)
                events.extend(node_events)

        return events

    def get_encoding_events(self, raw_data):
        # much like regular encoding, just also needs vertical position on screen 
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get('type', None) == 'encode':
                event = audio_keyboard_response_node(trialdata)
                events.extend(event)

        return events