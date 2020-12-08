# from report import ltpFR3_report
# from serialrec_report import serialrec_report
# from presrate_report import presrate_report
# from NFA_report import NFA_report 
# from survey_processing import process_survey
from post_process import ContainerFactory, CleanerFactory, ReporterFactory, psiturk_tools
import argparse
import os

# reports_func = {"serialrec": serialrec_report,
#                 "presrate": presrate_report,
#                 "NFA": NFA_report,
#                 # "ltpFR3": ltpFR3_report
#                 }

parser = argparse.ArgumentParser()
parser.add_argument("experiment")
parser.add_argument("data_root")
parser.add_argument("--db_path", default=None) 
parser.add_argument("--force", action='store_true', default=False)
parser.add_argument("--verbose", action='store_true', default=False)
parser.add_argument("--no-reports", action='store_true', default=False)
parser.add_argument("--no-events", action='store_true', default=False)
args = parser.parse_args()

exp = args.experiment

# root_dir = '/data/eeg/scalp/ltp/{}_MTurk/'.format(exp)
root_dir = os.path.join(args.data_root, exp)

paths_dict = {}

paths_dict["survey"] = os.path.join(root_dir, "survey_responses.csv")
paths_dict["root"] = root_dir
paths_dict["exp"] = exp
paths_dict["db"] = args.db_path
paths_dict["dictionary"] = os.path.join(root_dir, 'dictionary.txt')
paths_dict["wordpool"] = os.path.join(root_dir, 'wordpool.txt')

# Process json into pandas dataframe structures
data_container = ContainerFactory.get_container(paths_dict)

if args.force:
    print("Forcing event cleaning")

# Load the data from the psiTurk experiment database and process it into JSON files
if args.db_path is not None:
    psiturk_tools.load_psiturk_data(data_container, force=args.force, verbose=args.verbose)

if not args.no_events:
    data_cleaner = CleanerFactory.get_cleaner(data_container)
    data_cleaner.clean(force=args.force, verbose=args.verbose)

if not args.no_reports:
    # Generate a PDF report for each participant, along with an aggregate report and summary stats files
    report_generator = ReporterFactory.get_reporter(data_container)
    report_generator.run_reporting()
