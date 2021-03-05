from post_process.cleaning.experiment_cleaning import DataCleaner, trialdata_decorator
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

    @trialdata_decorator
    def get_encoding_events(self, record):

        if record.get("type", None) == "encoding":
            node_events = hold_keys_node(record)
            return node_events


    @trialdata_decorator
    def get_rest_events(self, record):
        if record.get("trial_type", None) == "hold-keys" \
                and record.get("type", None) == 'fixation':
                node_data, = hold_keys_node(record)
                node_data["type"] = "REST"
                return (node_data, )

    def add_repeats(self, events):

        repeat_mask = events.duplicated(subset=["type", "itemno"])

        events.loc[repeat_mask, "is_repeat"] = True
        events.loc[~repeat_mask, "is_repeat"] = False

        # FIXME: this could be a lot more readable
        # the purpose of this is to count every instance of a unique item presentation
        # and add te count to every event with that item, recalls included.
        # could potentially be improved with a groupby.count subtable

        for itemno in events[events["type"] == "WORD"]["itemno"].unique():
            events.loc[((events["type"] == "WORD") | (events["type"] == "REC_WORD"))
                       & (events["itemno"] == itemno), "repeats"] = len(events[(events["itemno"] == itemno)
                                                                               & (events["type"] == "WORD")])

        return events
