import psiturk_tools
from run_stats import run_stats
# from report import ltpFR3_report
from serialrec_report import serialrec_report
from presrate_report import presrate_report
from NFA_report import NFA_report 
from survey_processing import process_survey
from sort_excluded_files import sort_excluded_files
import argparse
import os

# TODO: get experiment and database names from command line

parser = argparse.ArgumentParser()
parser.add_argument("experiment")
# parser.add_argument("id_file")
parser.add_argument("data_root")
parser.add_argument("--db_path", default=None)
parser.add_argument("--table", default=None)
args = parser.parse_args()

exp = args.experiment
root_dir = '/data/eeg/scalp/ltp/{}_MTurk/'.format(exp)

paths_dict = {}

paths_dict["event"] = os.path.join(root_dir, "events")
paths_dict["data"] = os.path.join(root_dir, "data")
paths_dict["stats"] = os.path.join(root_dir, "stats")
paths_dict["reports"] = os.path.join(root_dir, "reports")
paths_dict["survey"] = os.path.join(root_dir, "survey_responses.csv")
paths_dict["root"] = root_dir

# Set paths
webster_path = 'webster_dictionary.txt'  # dictionary to use when looking for ELIs and correcting spelling

reports_func = {"serialrec": serialrec_report,
                "presrate": presrate_report,
                "NFA": NFA_report,
                # "ltpFR3": ltpFR3_report
                }



# Load the data from the psiTurk experiment database and process it into JSON files
if args.db_path != None and args.table != None:
    psiturk_tools.load_psiturk_data("sqlite:///" + args.db_path, args.table, paths_dict, force=False)
else:
    print("skipping database load")

# Create behavioral matrices from JSON data for each participant and save to JSON files
psiturk_tools.process_psiturk_data(paths_dict, webster_path, force=False)

# Update survey response database
process_survey(paths_dict)

# Generate a PDF report for each participant, along with an aggregate report and summary stats files
reports_func[args.experiment](paths_dict)
# ltpFR3_report(stat_dir, report_dir, force=False)

# Sort files for excluded, rejected, and bad session participants into the appropriate folders
sort_excluded_files(paths_dict)
