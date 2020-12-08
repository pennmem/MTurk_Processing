from post_process.cleaning.experiment_cleaning import DataCleaner, EventDecorators
from post_process.utils import progress_bar, strip_tags, change_key, filter_keys
from post_process.cleaning.plugin_processing import  free_sort_node, positional_html_display_node, hold_keys_check_node
import pandas as pd
import numpy as np


class OrderedRecallCleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)

        self.event_types = [self.get_internal_events,
                            self.get_encoding_events, 
                            self.get_recall_events]

        self.modifiers = [self.add_itemno,
                          self.add_list,
                          self.add_serialpos,
                          self.add_recalled]

    def get_recall_events(self, raw_data):
        # entirely different from normal recall, deals with both final recall and repositioning
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]

            if trialdata.get("type", None) == "recall":
                node_events = free_sort_node(trialdata)
                events.extend(node_events)

        return events

    def get_encoding_events(self, raw_data):
        # much like regular encoding, just also needs vertical position on screen 
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "encoding":
                event = positional_html_display_node(trialdata)

                events.extend(event)

        return events

    def get_hold_keys_events(self, raw_data):
        data = raw_data["data"]
        events = []

        for record in data:
            trialdata = record["trialdata"]
            
            if trialdata.get("type", None) == "check":
                node_events = hold_keys_check_node(trialdata)
                events.extend(node_events)

        return events

    def add_itemno(self, events):

        events.loc[events["type"] == 'WORD', "itemno"]  \
                = events.loc[events["type"] == 'WORD', "item"] \
                        .apply(lambda x: self.get_item_id(x))

        events.loc[events["type"] == 'END_RECALL', "itemnos"]  \
                = events.loc[events["type"] == 'END_RECALL', "end_positions"] \
                        .apply(lambda x: [self.get_item_id(item) for item in x])

        return events
    
    def add_recalled(self, events):
        '''
        '''
        events = events.sort_values("mstime")

        drop_events = events.query("type == 'DRAG' and mode == 'entering'") \
                            .drop_duplicates(subset=['item', 'listno'], keep='last')


        def find_rectime(row):
            drop = drop_events.query("item == @row['item'] and listno == @row['listno']")
            rt = drop["rt"]
            return rt.values[0]

        def find_recall(row):
            drop = drop_events.query("item == @row['item'] and listno == @row['listno']")
            tg = drop["target"]
            return tg.values[0] + 1

        events.loc[(events["type"] == "WORD"), "recalled"] = events.loc[(events["type"] == "WORD")].apply(find_recall, axis=1)
        events.loc[(events["type"] == "WORD"), "rt"] = events.loc[(events["type"] == "WORD")].apply(find_rectime, axis=1)
        events.loc[(events["type"] == "WORD"), "correct"] = (events.loc[(events["type"] == 'WORD'),"serialpos"] == (events.loc[(events["type"] == 'WORD'), "recalled"]))*1
        events.loc[(events["type"] == "WORD"), "distance"] = events.loc[(events["type"] == 'WORD'), "recalled"] - events.loc[(events["type"] == 'WORD'), "serialpos"]

        return events
