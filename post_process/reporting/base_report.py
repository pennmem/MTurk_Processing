from yattag import Doc
import os
from post_process.utils import progress_bar
from post_process.utils import get_timestamp
import importlib.resources as pkg_resources
import pandas as pd
import numpy as np

import post_process.resources as resources
import post_process.resources.css as css
import traceback as tb

# grab resources for reports
plotly = pkg_resources.read_text(resources, 'plotly.js')
skeleton = pkg_resources.read_text(css, 'skeleton.css')
normalize = pkg_resources.read_text(css, 'normalize.css')


class ReportFailedException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class BaseReporter():
    def __init__(self, data_container):
        self.data_container = data_container

    def generate_report(self, subject):
        raise NotImplementedError("This is an interface")

    def generate_average_report(self):
        raise NotImplementedError("This is an interface")

    @progress_bar()
    def run_reporting(self, force=False):
        subjects = self.data_container.get_subject_codes(cleaned=True)

        # TODO: only overwrite/regenerate report if force==True
        for i, sub in enumerate(subjects):
            yield i/len(subjects)

            try:
                odir = os.path.join(self.data_container.reports, sub + ".html")
                os.makedirs(os.path.split(odir)[0], exist_ok=True)
                with open(odir, 'w') as f:
                    f.write(self.generate_report(sub).write_report())
            # except ReportFailedException:
            except Exception as e:
                tb.print_exc()
                print(f"Failed to generate report for {sub}")

        try:
            # self.generate_average_report().write_report("average_report" + get_timestamp(), self.data_container.reports) replaced this code w the code below
            odir = os.path.join(self.data_container.reports, "average.html")
            os.makedirs(os.path.split(odir)[0], exist_ok=True)
            with open(odir, 'w') as f:
                f.write(self.generate_average_report().write_report())
        except ReportFailedException:
            print(f"Failed to generate average report")

        yield 1


class Report(object):
    def __init__(self, title):
        self.stats = {}
        self.figures = {}
        self.title = title

    def add_fig(self, title, fig):
        self.figures[title] = fig

    def add_stat(self, title, value):
        self.stats[title] = value

    def get_crp(self, df, list_length):
        df_trials = df['listno'].unique()
        crp_avg = pd.DataFrame()
        for trial in df_trials:
            beh = df.loc[df['listno'] == trial]
            crp = pd.DataFrame()
            crp['subject'] = beh['subject']
            crp['serialpos'] = beh['serialpos']
            crp['transitions'] = beh['serialpos'].diff()
            crp['irt'] = beh['mstime'].diff()
    
            crp = crp.query('transitions != 0')
            trans = crp['transitions'].to_numpy()
            trans = np.delete(trans, 0)
            irt = crp['irt'].to_numpy()
            irt = np.delete(irt, 0)

            irt_inplace = np.full(2 * list_length + 1, np.nan)
            for count, value in enumerate(trans):
                irt_inplace[int(value) + list_length] = irt[count]
            
            irt_inplace[0] = np.nan; irt_inplace[list_length] = np.nan; irt_inplace[list_length * 2] = np.nan

            pos = crp['serialpos'].to_numpy()
            lags = np.ones(list_length)
            pos_lags = np.zeros(2*list_length + 1)

            for p, _ in enumerate(pos):
                lags[int(pos[p])-1] = 0
                for l, _ in enumerate(lags):
                    if lags[l] != 0 and pos[p] != 0:
                        pos_lags[(l + 1) - int(pos[p]) + list_length] += 1 
            act_lags = np.zeros(2 * list_length + 1)
            for p, _ in enumerate(trans):
                for l in range(-1 * (list_length - 1), list_length):
                    if trans[p] == l and trans[p] != 0:
                        act_lags[l+list_length] += 1

            crp_array = np.divide(act_lags, pos_lags, out=np.zeros_like(act_lags),\
                    where = pos_lags != 0)
            crp_array[0] = np.nan; crp_array[list_length] = np.nan; crp_array[list_length * 2] = np.nan

            crp_df = pd.DataFrame()
            subject = crp['subject'].unique()
            sub_array = np.full(len(crp_array), subject)
            crp_df['Subject'] = pd.Series(sub_array)
            crp_df['Lags'] = pd.Series(range(-1 * list_length, list_length + 1))
            crp_df['Conditional Response Probability'] = pd.Series(crp_array)
            trial_array = np.full(len(crp_array), trial)
            crp_df['Trial'] = pd.Series(trial_array)
            crp_df['Conditional Response Latency'] = pd.Series(irt_inplace)
            
            crp_avg = crp_avg.append(crp_df)

        return crp_avg

    def write_report(self):
        doc, tag, text, line = Doc().ttl()

        # TODO: link barebones css

        doc.asis('<!DOCTYPE html>')
        with tag('head'):
            with tag('style'):
                doc.asis(skeleton)
                doc.asis(normalize)

            with tag('script'):
                doc.asis(plotly)

        with tag('html'):
            with tag('body'):
                line('h1', self.title)
                line('h2', 'Session Statistics')
                with tag('table', klass="u-full-width"):
                    with tag('tbody'):
                        for label, stat in self.stats.items():
                            with tag("tr"):
                                line("td", label)
                                line("td", stat)

                line('h2', 'Session Figures')
                with tag('div', id='figs', klass='u-full-width'):
                    with tag('figure'):
                        for label, fig in self.figures.items():
                            line("figcaption", label)
                            doc.asis(fig)
        
        return doc.getvalue()
