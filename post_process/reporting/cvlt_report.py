from glob import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from pybeh import spc, positional_crp
from post_process.reporting.base_report import BaseReporter, Report 
from post_process.utils import pad_to_dense
import plotly.express as px


class CVLTReport(BaseReporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_report(self, subject):
        report = Report(subject + ' CVLT-DFR Report')
        data = self.data_container.get_cleaned_data(subject) 
        pd.set_option("display.max_columns", None, "display.max_rows", None)
        # generate spc
        beh = data.loc[data["type"] == 'WORD']
        cvlt = beh.loc[beh['phase'] == 'CVLT']
        cvlt = cvlt.loc[cvlt['listtype'] == 'List A']
        cvlt_scurve_data = cvlt.groupby('serialpos').mean()
        
        cvlt_scurve = px.line(cvlt_scurve_data.reset_index(), x='serialpos', y='recalled',
                labels={
                        'serialpos': 'Serial Position',
                        'recalled': 'Recall Probability (%)'
                }) \
                .to_html(full_html=False, include_plotlyjs=False)
        
        report.add_fig(subject + ' CVLT Serial Position Curve', cvlt_scurve)
        
        #generate stats
        cvlt_recalled = cvlt.groupby('listno').mean()
        cvlt_recalled = cvlt_recalled.reset_index()
        cvlt_mean_recalled = cvlt_recalled['recalled'].mean()

        cvlt_mean_recalled = round(cvlt_mean_recalled, 3) * 100

        report.add_stat(subject + "'s CVLT Recall Probability", cvlt_mean_recalled)
        
        # generate lag-crp and lag-crl
        beh = data.loc[data['type'] == 'REC_WORD']
        cvlt = beh.loc[beh['phase'] == 'CVLT']
        cvlt = cvlt.query('serialpos != -1.0')        

        cvlt_crp_df = pd.DataFrame()

        cvlt_crp_df = report.get_crp(cvlt, 16)
    
        cvlt_crp_df_avg = cvlt_crp_df.groupby('Lags').mean()
        cvlt_crp_df_avg = cvlt_crp_df_avg.reset_index()
                
        cvlt_lag_crp_curve = px.line(cvlt_crp_df_avg, x='Lags', y='Conditional Response Probability') \
                .to_html(full_html=False, include_plotlyjs=False)

        cvlt_lag_crl_curve = px.line(cvlt_crp_df_avg, x='Lags', y='Conditional Response Latency')\
                .to_html(full_html=False, include_plotlyjs=False)

        report.add_fig(subject + ' CVLT Lag-CRP Curve', cvlt_lag_crp_curve)
        report.add_fig(subject + ' CVLT Lag-CRL Curve', cvlt_lag_crl_curve)
                
        # implement IRT plot

        return report

    def generate_average_report(self):
        report = Report('Average CVLT Report')
        data = self.data_container.get_cleaned_data()

        # generate spc
        beh = data.loc[data["type"] == 'WORD']
        cvlt = beh.loc[beh['phase'] == 'CVLT']
        cvlt = cvlt.loc[cvlt['listtype'] == 'List A']
        cvlt_scurve_data = cvlt.groupby(['subject', 'serialpos']).mean().reset_index() * 100
        cvlt_sem = cvlt_scurve_data.groupby('serialpos').sem()
        cvlt_mean = cvlt_scurve_data.groupby('serialpos').mean()
        cvlt_mean['sem'] = cvlt_sem['recalled']
        pd.set_option("display.max_columns", None)
        
        

        cvlt_scurve = px.line(cvlt_mean.reset_index(), x='serialpos', y='recalled', error_y='sem',
                labels={
                        'serialpos': 'Serial Position',
                        'recalled': 'Recall Probability (%)'
                }) \
                .to_html(full_html=False, include_plotlyjs=False)
        
        # generate summary statistics
        csv = os.path.join(self.data_container.reports, "correlations.csv")
        cvlt_recalled_by_sub = cvlt.groupby(['subject', 'listno']).mean().reset_index()
        cvlt_recalled = cvlt_recalled_by_sub.groupby('subject').mean()
        cvlt_recalled = cvlt_recalled.reset_index()
        corr_df = pd.DataFrame()
        corr_df['subject'] = cvlt_recalled['subject']
        corr_df['recalled'] = cvlt_recalled['recalled']
        
        corr_df.to_csv(csv)

        cvlt_mean_recalled = cvlt_recalled['recalled'].mean()

        cvlt_mean_recalled = round(cvlt_mean_recalled, 3) * 100

        report.add_stat('Average CVLT Recall Probability (%)', cvlt_mean_recalled)

        # generate correlation summary

        # added report here for appearances
        report.add_fig('Average CVLT Serial Position Curve', cvlt_scurve)
       
        # generate lag-crp
        beh = data.loc[data['type'] == 'REC_WORD']
        cvlt = beh.loc[beh['phase'] == 'CVLT']
        cvlt = cvlt.query('serialpos != -1.0')
        
        sub = cvlt['subject'].unique()
        cvlt_by_sub = pd.DataFrame()
        cvlt_crp_by_sub = pd.DataFrame()
        for subject in sub:
                cvlt_by_sub = cvlt.loc[cvlt['subject'] == subject]
                cvlt_crp_by_sub = cvlt_crp_by_sub.append(report.get_crp(cvlt_by_sub, 16))
        aggregate_cvlt_crp = pd.DataFrame()

        aggregate_cvlt_crp = cvlt_crp_by_sub.groupby('Lags').mean().reset_index()
        aggregate_cvlt_crp_sem = cvlt_crp_by_sub.groupby('Lags').sem().reset_index()
        
        aggregate_cvlt_crp['crp sem'] = aggregate_cvlt_crp_sem['Conditional Response Probability']
        aggregate_cvlt_crp['crl sem'] = aggregate_cvlt_crp_sem['Conditional Response Latency']

        aggregate_cvlt_crp_curve = px.line(aggregate_cvlt_crp, x='Lags', y='Conditional Response Probability', error_y='crp sem') \
                .to_html(full_html=False, include_plotlyjs=False)

        aggregate_cvlt_crl_curve = px.line(aggregate_cvlt_crp, x='Lags', y='Conditional Response Latency', error_y='crl sem') \
                .to_html(full_html=False, include_plotlyjs=False)

        report.add_fig('Aggregate CVLT Lag-CRP Curve', aggregate_cvlt_crp_curve)

        report.add_fig('Aggregate CVLT Lag-CRL Curve', aggregate_cvlt_crl_curve)

        return report
