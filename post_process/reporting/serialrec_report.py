import numpy as np
import pandas as pd
from pybeh import spc, positional_crp
from post_process.reporting.base_report import BaseReporter, Report 
from post_process.utils import pad_to_dense

class SerialRecallReport(BaseReporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_report(self, subject):
        report = Report(f"{subject} - Serial Recall")
        data = self.data_container.get_cleaned_data(subject) 

        # generate spc
        beh_mat = data.loc[data["type"] == 'REC_WORD'].groupby("listno").serialpos.apply(np.array)
        beh_mat = pad_to_dense(beh_mat.values, value=np.nan)

        # TODO: max list length
        # print(spc.spc( beh_mat, list(range(len(beh_mat))), 16))
        # spc_fig = spc()

        # generate crp

        # generate summary statistics
        rec_prob = data.loc[data["type"] == 'WORD', 'recalled'].sum() / len(data.loc[data["type"] == 'WORD'].index)
        report.add_stat("Recall Probability", rec_prob)

        return report

    def generate_average_report(self):
        report = Report()
        data = self.data_container.get_cleaned_data()

        # generate spc

        # generate crp

        # generate summary statistics
        

        return report
