from post_process import DataContainer, get_cleaner, get_reporter, psiturk_tools
import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument("experiment", help='The name of the experiment. If db_path is supplied, this must match the name of the table containing experiment data in the database.')
parser.add_argument("data_root", help='Root directory from which all data destination paths are referenced.')
parser.add_argument("--db_path", default=None, help="Path to experiment database, needed if data is not already extracted and anonymized. This path should be formatted as a URI, with file:/// prepended to both relative and absolute paths.")
parser.add_argument("--force", action='store_true', default=False, help='Overwrite existing files')
parser.add_argument("--verbose", action='store_true', default=False, help="Add this switch to increase the amount of output during processing, including errors.")
parser.add_argument("--no-reports", action='store_true', default=False, help="Add this switch to prevent reports from being run.")
parser.add_argument("--no-events", action='store_true', default=False, help="Add this switch to prevent events from being run.")
args = parser.parse_args()

exp = args.experiment.strip()

paths_dict = {}

paths_dict["survey"] = "survey_responses.csv"
paths_dict["root"] = args.data_root
paths_dict["experiment"] = exp
paths_dict["db"] = args.db_path
paths_dict["dictionary"] = 'dictionary.txt'
paths_dict["wordpool"] = 'wordpool.txt'
paths_dict["class_exp"] = 'class_' in exp

if not exp:
    print('exp is blank!')
    sys.exit(-1)

# Process json into pandas dataframe structures
data_container = DataContainer(**paths_dict)

if args.force:
    print("Forcing event cleaning")

# Load the data from the psiTurk experiment database and process it into JSON files
if args.db_path is not None:
    psiturk_tools.load_psiturk_data(data_container, force=args.force, verbose=args.verbose)

if not args.no_events:
    data_cleaner = get_cleaner(data_container)
    data_cleaner.clean(force=args.force, verbose=args.verbose)

if not args.no_reports:
    # Generate a PDF report for each participant, along with an aggregate report and summary stats files
    report_generator = get_reporter(data_container)
    report_generator.run_reporting()
