from post_process.cleaning.experiment_cleaning import DataCleaner, trialdata_decorator
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

    @trialdata_decorator
    def get_recall_events(self, record):
        # entirely different from normal recall, deals with both final recall and repositioning

        if record.get("type", None) == "recall":
            return free_sort_node(record)

    @trialdata_decorator
    def get_encoding_events(self, record):
        # much like regular encoding, just also needs vertical position on screen 
        if record.get("type", None) == "encoding":
            return positional_html_display_node(record)

    @trialdata_decorator
    def get_hold_keys_events(self, record):
            if record.get("type", None) == "check":
                return hold_keys_check_node(record)

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
            try:
                tg = drop["target"].values[0] + 1
                return tg
            except Exception as e:
                print("error finding target")
                print(drop)
                raise(e)

        events.loc[(events["type"] == "WORD"), "recalled"] = events.query("type == 'WORD'").apply(find_recall, axis=1)
        events.loc[(events["type"] == "WORD"), "rt"] = events.query("type == 'WORD'").apply(find_rectime, axis=1)
        events.loc[(events["type"] == "WORD"), "correct"] = (events.query("type == 'WORD'")["serialpos"] == (events.query("type == 'WORD'")["recalled"]))*1
        events.loc[(events["type"] == "WORD"), "distance"] = events.query("type == 'WORD'")["recalled"] - events.query("type == 'WORD'")["serialpos"]
        events.loc[(events["type"] == "WORD"), "relative_correct"] = events.query("type == 'WORD'").groupby('listno')["recalled"].diff().fillna(events["recalled"]) == 1

        return events


    def exclude_subject(self, events, recall_thresh=.95, no_recalls_thresh=1, allowed_lapse=1000):
        recalls_by_list = events[(events["type"] == 'WORD')].groupby("listno")["correct"].sum()
        presentations = len(events[(events["type"] == 'WORD')].index)
        all_recalls = np.sum(recalls_by_list)

        if all_recalls >= presentations * recall_thresh:
            return True 

        no_recall_lists = np.sum(recalls_by_list.values == 0)
        if no_recall_lists > no_recalls_thresh:
            return True

        # lost focus // single query had unhashable type error, though chained version doesn't
        focus = events.query("type == 'focus'").query("value == 'on'").query("interval > 0").query("mstime > 0")
        if len(focus):

            focus_intervals = [pd.Interval(row.mstime - row['interval'], row['mstime']) for i, row in focus.iterrows()]
            list_intervals  = [pd.Interval(left, right) for left, right in zip(events.query("type == 'WORD' & serialpos == 1")['mstime'], events.query("type == 'END_RECALL'")['mstime'])]

            bad_lists = 0
            for list_interval in list_intervals:
                for focus_interval in focus_intervals:
                    if list_interval.overlaps(focus_interval) and focus_interval.length > allowed_lapse:
                        bad_lists += 1
                        break

            if bad_lists > 12: return True 

        return False
