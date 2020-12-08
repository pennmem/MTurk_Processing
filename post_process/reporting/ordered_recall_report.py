import numpy as np
import pandas as pd
import math
from post_process.reporting.base_report import BaseReporter, Report 
import plotly.express as px


class OrderedRecallReport(BaseReporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_report(self, subject):
        report = Report(f"{subject} - Ordered Recall")

        data = self.data_container.get_cleaned_data(subject).query("type in ['WORD'] and listno >= 3")

        pivot = data.pivot_table(index=['listno', 'length'], \
                         columns='serialpos',                   \
                         values=['rt', 'recalled', 'correct', 'distance'])  \

        all_lists = pivot.groupby(["length"]) \
                         .mean()

        fig = px.line(all_lists.stack().reset_index(), x='serialpos', y='correct', color='length') \
                .to_html(full_html=False, include_plotlyjs=False)
        report.add_fig("Serial Position Curve", fig)

        fig = px.line(all_lists.stack().reset_index(), x='serialpos', y='rt', color='length') \
                .to_html(full_html=False, include_plotlyjs=False)
        report.add_fig("Response Time", fig)

        # # error distances
        # report.add_fig("error_distances", plot_error(get_error(data)))

        # conditions
        report.add_stat("Condition", str(data["condition"].values[0]))

        # % correct
        report.add_stat("Recall Proportion", f"{data['correct'].mean():.2f}" )

        return report

    def generate_average_report(self):
        return Report()

