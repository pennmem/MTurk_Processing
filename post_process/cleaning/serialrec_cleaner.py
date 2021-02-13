from post_process.cleaning.experiment_cleaning import DataCleaner, trialdata_decorator
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


    @trialdata_decorator
    def get_encoding_events(self, record):
        if record.get("type", None) == "encoding":
            node_events = hold_keys_node(record)
            return node_events
