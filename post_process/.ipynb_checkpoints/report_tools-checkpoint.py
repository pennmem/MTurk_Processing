from glob import glob
import pandas as pd
import os
import json
from psiturk_tools import _read_raw_json

def load_clean_events(paths_dict):
    # TODO: need to read json not as dataframe
    files = glob(os.path.join(paths_dict["event"],'MTK*.json'))
    bad_subs = get_bad_subs(paths_dict)
    
    files = [f for f in files if os.path.basename(f).split('.')[0] not in bad_subs]
    
    return _read_raw_json(files)

def load_all_events(paths_dict):
    # TODO: need to read json not as dataframe
    files = glob(os.path.join(paths_dict["event"],'MTK*.json'))
    return _read_raw_json(files)

def load_clean_data(paths_dict):
    files = glob(os.path.join(paths_dict["data"],'MTK*.json'))
    bad_subs = get_bad_subs(paths_dict)
    
    files = [f for f in files if os.path.basename(f).split('.')[0] not in bad_subs]
    
    return _read_saved_dataframes(files)

def load_all_data(paths_dict):
    files = glob(os.path.join(paths_dict["data"],'MTK*.json'))
    return _read_saved_dataframes(files)

def load_survey_data():
    pass


def _read_saved_dataframes(files):
    all_data = []
    for f in files:
        all_data.append(pd.read_json(f))
    
    return pd.concat(all_data)




def _flatten_dict(dd, separator ='_', prefix =''): 
    return { prefix + separator + k if prefix else k : v 
             for kk, vv in dd.items() 
             for k, v in _flatten_dict(vv, separator, kk).items() 
             } if isinstance(dd, dict) else { prefix : dd } 

def get_bad_subs(paths_dict):
    EXCLUDED = os.path.join(paths_dict['root'], 'EXCLUDED.txt')
    BAD_SESS = os.path.join(paths_dict['root'], 'BAD_SESS.txt')
    REJECTED = os.path.join(paths_dict['root'], 'REJECTED.txt')
    WROTE_NOTES = os.path.join(paths_dict['root'], 'WROTE_NOTES.txt')
    
    with open(EXCLUDED, 'r') as f:
        exc = [s.strip() for s in f.readlines()]
    
    with open(BAD_SESS, 'r') as f:
        bad_sess = [s.strip() for s in f.readlines()]
    
    with open(REJECTED, 'r') as f:
        rej = [s.strip() for s in f.readlines()]
    
    with open(WROTE_NOTES, 'r') as f:
        notes = [s.strip() for s in f.readlines()]

    return exc + bad_sess + rej + notes

def get_all_subs(paths_dict):
    pass

def get_cleaned_subs(paths_dict):
    pass


def which_item(recall, presented, when_presented, dictionary):
    """
    Determine the serial position of a recalled word. Extra-list intrusions are identified by looking them up in a word
    list. Unrecognized words are spell-checked.

    :param recall: A string typed by the subject into the recall entry box
    :param presented: The list of words seen by this subject so far, across all trials <= the current trial number
    :param when_presented: A listing of which trial each word was presented in
    :param dictionary: A list of strings that should be considered as possible extra-list intrusions
    :return: If a correct recall or PLI, returns the trial number and serial position of the word's presentation, plus
    the spelling-corrected version of the recall. If an ELI or invalid entry, returns a trial number of None, a serial
    position of -999, and the spelling-corrected version of the recall.
    """

    # Check whether the recall exactly matches a previously presented word
    seen, seen_where = self_term_search(recall, presented)

    # If word has been presented
    if seen:
        # Determine the list number and serial position of the word
        list_num = when_presented[seen_where]
        first_item = np.min(np.where(when_presented == list_num))
        serial_pos = seen_where - first_item + 1
        return int(list_num), int(serial_pos), recall

    # If the recalled word was not presented, but exactly matches any word in the dictionary, mark as an ELI
    in_dict, where_in_dict = self_term_search(recall, dictionary)
    if in_dict:
        return None, -999, recall

    # If the recall contains non-letter characters
    if not recall.isalpha():
        return None, -999, recall

    # If word is not in the dictionary, find the closest match based on edit distance
    recall = correct_spelling(recall, presented, dictionary)
    return which_item(recall, presented, when_presented, dictionary)


def self_term_search(find_this, in_this):
    for index, word in enumerate(in_this):
        if word == find_this:
            return True, index
    return False, None


# def correct_spelling(recall, presented, dictionary):
#
#     # edit distance to each item in the pool and dictionary
#     dist_to_pool = damerau_levenshtein_distance_ndarray(recall, np.array(presented))
#     dist_to_dict = damerau_levenshtein_distance_ndarray(recall, np.array(dictionary))
#
#     # position in distribution of dist_to_dict
#     ptile = np.true_divide(sum(dist_to_dict <= np.amin(dist_to_pool)), dist_to_dict.size)
#
#     # decide if it is a word in the pool or an ELI
#     if ptile <= .1:
#         corrected_recall = presented[np.argmin(dist_to_pool)]
#     else:
#         corrected_recall = dictionary[np.argmin(dist_to_dict)]
#     recall = corrected_recall
#     return recall


def pad_into_array(l):
    """
    Turn an array of uneven lists into a numpy matrix by padding shorter lists with zeros. Modified version of a
    function by user Divakar on Stack Overflow, here:
    http://stackoverflow.com/questions/32037893/numpy-fix-array-with-rows-of-different-lengths-by-filling-the-empty-elements-wi

    :param l: A list of lists
    :return: A numpy array made from l, where all rows have been made the same length via padding
    """
    l = np.array(l)
    # Get lengths of each row of data
    lens = np.array([len(i) for i in l])

    # If l was empty, we can simply return the empty numpy array we just created
    if len(lens) == 0:
        return lens

    # If all rows were the same length, just return the original input as an array
    if lens.max() == lens.min():
        return l

    # Mask of valid places in each row
    mask = np.arange(lens.max()) < lens[:, None]

    # Setup output array and put elements from data into masked positions
    out = np.zeros(mask.shape, dtype=l.dtype)
    out[mask] = np.concatenate(l)

    return out


def recalls_to_intrusions(rec):
    """
    Convert a recalls matrix to an intrusions matrix. In the recalls matrix, ELIs should be denoted by -999 and PLIs
    should be denoted by -n, where n is the number of lists back the word was originally presented. All positive numbers
    are assumed to be correct recalls. The resulting intrusions matrix denotes correct recalls by 0, ELIs by -1, and
    PLIs by n, where n is the number of lists back the word was originally presented.

    :param rec: A lists x items recalls matrix, which is assumed to be a numpy array
    :return: A lists x items intrusions matrix
    """
    intru = rec.copy()
    # Set correct recalls to 0
    intru[np.where(intru > 0)] = 0
    # Convert negative numbers for PLIs to positive numbers
    intru *= -1
    # Convert ELIs to -1
    intru[np.where(intru == 999)] = -1
    return intru