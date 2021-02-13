from yattag import Doc
import os
from post_process.utils import progress_bar
from post_process.utils import get_timestamp
import importlib.resources as pkg_resources

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

    # TODO: lost focus plot

    @progress_bar()
    def run_reporting(self, force=False):
        subjects = self.data_container.get_subject_codes(cleaned=True)

        # TODO: only overwrite/regenerate report if force==True
        for i, sub in enumerate(subjects):
            yield i/len(subjects)

            try:
                odir = os.path.join(self.data_container.reports, sub + ".html")
                os.makedirs(os.path.split(odir)[0], exist_ok=True)
                # TODO: move io to data_container
                with open(odir, 'w') as f:
                    f.write(self.generate_report(sub).write_report())
            # except ReportFailedException:
            except Exception as e:
                tb.print_exc()
                print(f"Failed to generate report for {sub}")

        # try:
        #     self.generate_average_report().write_report("average_report" + get_timestamp(), self.data_container.reports)
        # except ReportFailedException:
        #     print(f"Failed to generate average report")

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

    def write_report(self):
        doc, tag, text, line = Doc().ttl()

        doc.asis('<!DOCTYPE html>')
        with tag('head'):
            with tag('style'):
                doc.asis(skeleton) # basic CSS
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
