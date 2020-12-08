from post_process.cleaning.experiment_cleaning import DataCleaner, EventDecorators
from post_process.utils import progress_bar, strip_tags, change_key, filter_keys
import pandas as pd
import numpy as np
from post_process.cleaning.plugin_processing import free_recall_node, hold_keys_node, hold_keys_check_node

class SerialRecCleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)
        self.event_types = [self.get_internal_events,
                        self.get_encoding_events, 
                        self.get_recall_events]

        self.modifiers = [self.add_itemno,
                          self.add_list,
                          self.add_list_length,
                          self.expand_conditions,
                          self.add_serialpos,
                          self.correct_recalls,
                          self.add_recalled,
                          self.add_recalled_serialpos,
                          self.add_intrusion]

    # def get_recall_events(self, raw_data):
    #     '''
    #     Break nodes of type free-recall into recall events with timestamps

    #     TODO: this method is largely repeated and should really have the bulk of the functionality
    #            inherited
    #     '''
        
    #     data = raw_data["data"]
    #     events = []
    #     for record in data:
    #         trialdata = record["trialdata"]

    #         if trialdata.get("type", None) == "recall":
    #             node_events = free_recall_node(trialdata)
    #             events.extend(node_events)

    #     return events

    def get_encoding_events(self, raw_data):
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "encoding":
                node_events = hold_keys_node(trialdata)
                events.extend(node_events)

        return events
