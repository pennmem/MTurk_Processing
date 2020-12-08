import numpy as np
import pandas as pd
import math
from post_process.reporting.base_report import BaseReporter, Report 
from post_process.utils import pad_to_dense
import matplotlib.pyplot as mp
import plotly.express as px

class RepFRReport(BaseReporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_report(self, subject):
        report = Report(f"{subject} - RepFR")
        data = self.data_container.get_cleaned_data(subject)

        recalls_by_repeat = data[data.type == 'WORD'].groupby(["repeats", "serialpos"]).recalled.mean()

        new_index = pd.MultiIndex.from_product(recalls_by_repeat.index.levels)
        recalls_by_repeat = recalls_by_repeat.reindex(new_index)
        recalls_by_repeat = recalls_by_repeat.fillna(np.nan)

        recall_prop = data[data.type == 'WORD'].query("4 <= serialpos <= 24").groupby(["subject", "repeats"]).recalled.mean()

        fig = px.histogram(recall_prop.reset_index(), x='repeats', y='recalled') \
                .to_html(full_html=False, include_plotlyjs=False)
        report.add_fig("Recall Histogram", fig)
        
        fig = px.line(recalls_by_repeat.reset_index(), x='serialpos', y='recalled', color='repeats') \
                .to_html(full_html=False, include_plotlyjs=False)
        report.add_fig("Serial Position", fig)


        # report.add_stat("1p Recall", )
        # report.add_stat("2p Recall", )
        # report.add_stat("3p Recall", )

        return report

