from glob import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from pybeh import spc, positional_crp
from post_process.reporting.base_report import BaseReporter, Report 
from post_process.utils import pad_to_dense
import plotly.express as px


class FR1Report(BaseReporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_report(self, subject):
        report = Report(subject + ' FR1 Report')
        data = self.data_container.get_cleaned_data(subject) 
        pd.set_option("display.max_columns", None)
        # generate spc
        beh = data.loc[data["type"] == 'WORD']
        fr1 = beh.loc[beh['phase'] == 'FR1']
        fr1_scurve_data = fr1.groupby('serialpos').mean()
        
        fr1_scurve = px.line(fr1_scurve_data.reset_index(), x='serialpos', y='recalled',
                labels={
                        'serialpos': 'Serial Position',
                        'recalled': 'Recall Probability (%)'
                }) \
                .to_html(full_html=False, include_plotlyjs=False)

        report.add_fig(subject + ' FR1 Serial Position Curve', fr1_scurve)
        
        #generate stats
        fr1_recalled = fr1.groupby('listno').mean()
        fr1_recalled = fr1_recalled.reset_index()
        fr1_mean_recalled = fr1_recalled['recalled'].mean()
        fr1_mean_recalled = round(fr1_mean_recalled, 3) * 100
        report.add_stat(subject + "'s FR1 Recall Probability", fr1_mean_recalled)
        

        # generate lag-crp and lag-crl
        beh = data.loc[data['type'] == 'REC_WORD']
        fr1 = beh.loc[beh['phase'] == 'FR1']
        fr1 = fr1.query('serialpos != -1.0')

        fr1_crp_df = pd.DataFrame()
        fr1_crp_df = report.get_crp(fr1, 12)
        fr1_crp_df_avg = fr1_crp_df.groupby('Lags').mean()
        fr1_crp_df_avg = fr1_crp_df_avg.reset_index()

        fr1_lag_crp_curve = px.line(fr1_crp_df_avg, x='Lags', y='Conditional Response Probability') \
                .to_html(full_html=False, include_plotlyjs=False)

        fr1_lag_crl_curve = px.line(fr1_crp_df_avg, x='Lags', y='Conditional Response Latency')\
                .to_html(full_html=False, include_plotlyjs=False)

        report.add_fig(subject + ' FR1 Lag-CRP Curve', fr1_lag_crp_curve)
        report.add_fig(subject + ' FR1 Lag-CRL Curve', fr1_lag_crl_curve)
                
        # implement IRT plot

        return report

    def generate_average_report(self):
        report = Report('Average FR1 Report')
        data = self.data_container.get_cleaned_data()

        # generate spc
        beh = data.loc[data["type"] == 'WORD']
        fr1 = beh.loc[beh['phase'] == 'FR1']

        fr1_scurve_data = fr1.groupby(['subject', 'serialpos']).mean().reset_index() * 100
        fr1_sem = fr1_scurve_data.groupby('serialpos').sem()
        fr1_mean = fr1_scurve_data.groupby('serialpos').mean()
        fr1_mean['sem'] = fr1_sem['recalled']
        pd.set_option("display.max_columns", None)
        
        fr1_scurve = px.line(fr1_mean.reset_index(), x='serialpos', y='recalled', error_y='sem',
                labels={
                        'serialpos': 'Serial Position',
                        'recalled': 'Recall Probability (%)'
                }) \
                .to_html(full_html=False, include_plotlyjs=False)

        # generate summary statistics
        fr1_recalled_by_sub = fr1.groupby(['subject', 'listno']).mean().reset_index()
        fr1_recalled = fr1_recalled_by_sub.groupby('subject').mean()
        fr1_recalled = fr1_recalled.reset_index()
        corr_df = pd.DataFrame()
        corr_df['subject'] = fr1_recalled['subject']
        corr_df['recalled'] = fr1_recalled['recalled']
        
        csv = os.path.join(self.data_container.reports, "correlations.csv")
        corr_df.to_csv(csv)
        fr1_mean_recalled = fr1_recalled['recalled'].mean()        
        fr1_mean_recalled = round(fr1_mean_recalled, 3) * 100
        report.add_stat('Average FR1 Recall Probability (%)', fr1_mean_recalled)

        # generate correlation summary
        

        # added report here for appearances
        report.add_fig('Average FR1 Serial Position Curve', fr1_scurve)

        # generate lag-crp
        beh = data.loc[data['type'] == 'REC_WORD']
        fr1 = beh.loc[beh['phase'] == 'FR1']
        fr1 = fr1.query('serialpos != -1.0')

        sub = fr1['subject'].unique()
        fr1_by_sub = pd.DataFrame()
        fr1_crp_by_sub = pd.DataFrame()
        for subject in sub:
                fr1_by_sub = fr1.loc[fr1['subject'] == subject]
                fr1_crp_by_sub = fr1_crp_by_sub.append(report.get_crp(fr1_by_sub, 12))
        aggregate_fr1_crp = pd.DataFrame()

        aggregate_fr1_crp = fr1_crp_by_sub.groupby('Lags').mean().reset_index()
        aggregate_fr1_crp_sem = fr1_crp_by_sub.groupby('Lags').sem().reset_index()

        aggregate_fr1_crp['crp sem'] = aggregate_fr1_crp_sem['Conditional Response Probability']
        aggregate_fr1_crp['crl sem'] = aggregate_fr1_crp_sem['Conditional Response Latency']

        aggregate_fr1_crp_curve = px.line(aggregate_fr1_crp, x='Lags', y='Conditional Response Probability', error_y='crp sem') \
                .to_html(full_html=False, include_plotlyjs=False)

        aggregate_fr1_crl_curve = px.line(aggregate_fr1_crp, x='Lags', y='Conditional Response Latency', error_y='crl sem') \
                .to_html(full_html=False, include_plotlyjs=False)
        
        report.add_fig('Aggregate FR1 Lag-CRP Curve', aggregate_fr1_crp_curve)

        report.add_fig('Aggregate FR1 Lag-CRL Curve', aggregate_fr1_crl_curve)
        

        # # implement prior list intrusion
        # beh = data.loc[data['type'] == 'REC_WORD']
        # fr1 = beh.loc[beh['phase'] == 'FR1']
        # lists = fr1['listno'].unique()
        # first_list = lists[0]
        # listno = fr1['listno'].to_numpy()
        # trials = listno - first_list
        # trials_series = pd.Series(trials)
        # fr1 = fr1.reset_index()
        # fr1['trials'] = trials_series
        # fr1 = fr1.query('intrusion > 0')
        # fr1 = fr1.query('trials > 9')
        # if len(fr1) > 0:
        #         fr1 = fr1.reset_index(drop = True)
        # length = len(fr1)
        # fr1['counting'] = pd.Series(np.full(length, 1.0))
        # fr1 = fr1.groupby('intrusion').sum()
        

        return report
