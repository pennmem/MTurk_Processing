from collections.abc import Iterable
from argparse import ArgumentParser
from functools import reduce
from itertools import product, cycle
from gensim.models import KeyedVectors
from random import shuffle
import gensim as gs
import numpy as np
import pandas as pd
# import nltk
# nltk.download('cmudict')

from nltk.corpus import cmudict
import time

d = cmudict.dict()

class NLP(object):
    '''
    namespace to group NLP tasks and NLP tasks requiring heavy disk IO
    '''
    model = None
    model_path = './model/googlenews_word2vec.bin.gz'

    @staticmethod
    def nsyl(word):
        try:
            ret = [len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]]
            # print(ret)
            return ret[0]
        except KeyError:
            #if word not found in cmudict
            return NLP._syllables(word)

    @staticmethod
    def _syllables(word):
        #referred from stackoverflow.com/questions/14541303/count-the-number-of-syllables-in-a-word
        count = 0
        vowels = 'aeiouy'
        word = word.lower()
        if word[0] in vowels:
            count +=1
        for index in range(1,len(word)):
            if word[index] in vowels and word[index-1] not in vowels:
                count +=1
        if word.endswith('e'):
            count -= 1
        if word.endswith('le'):
            count += 1
        if count == 0:
            count += 1
        return count

    @staticmethod
    def _load_word2vec(path):
        print("Loading word2vec model")
        NLP.model = KeyedVectors.load_word2vec_format(path, binary=True)
        print("Loaded word2vec model")

    @staticmethod
    def _delete_word2vec():
        ''' 
        save RAM by deleting model when we think we're done with it, 
        as usually we only need one distance matrix
        '''
        print("Deleting word2vec model")
        del NLP.model
        NLP.model = None

    @staticmethod
    def word_distance(word1, word2):
        if NLP.model is None:
            NLP._load_word2vec(NLP.model_path)

        return NLP.model.distance(word1, word2)

    @staticmethod
    def check_vocabulary(wordlist):
        word_vectors = NLP.model.wv;
        for word in wordlist:
            if word not in word_vectors.vocab:
                print(word)

    @staticmethod
    def distance_matrix(wordlist, delete=False, check=True):
        if check:
            if NLP.model is None:
                NLP._load_word2vec(NLP.model_path)

            NLP.check_vocabulary(wordlist)


        try:
            arr = np.asarray([[NLP.word_distance(w1, w2) for w2 in wordlist] for w1 in wordlist])

            if delete:
                NLP._delete_word2vec()

            return pd.DataFrame(arr, columns=wordlist, index=wordlist)
        except:
            raise Exception(f"{w1} or {w2} not in training corpus")

    @staticmethod
    def load_distance_matrix(filename):
        try:
            return pd.read_pickle(filename)
        except:
            raise Exception("Error reading distance matrix")

    @staticmethod
    def save_distance_matrix(mat, filename):
        mat.to_pickle(filename)


class Criteria(object):
    def __init__(self):
        pass

    def filter(self, partial_list, unused, used):
        raise NotImplementedError("Subclass this interface to provide filtering behavior")


class MatchCriteria(Criteria):
    def __init__(self, *args):
        self.criteria_list = [a for a in args]

    def filter(self, partial_list, unused, used):
        return reduce( lambda a, b: np.intersect1d(a, b), 
                  map( lambda x: x.filter(partial_list, unused, used), self.criteria_list))


class MaxSyllableCriteria(Criteria):
    def __init__(self, allow_used=False, thresh=2):
        self.thresh = thresh
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        return np.asarray([w for w in candidates if NLP.nsyl(w) <= self.thresh])


class MinSyllableCriteria(Criteria):
    def __init__(self, allow_used=False, thresh=2):
        self.thresh = thresh
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        return np.asarray([w for w in candidates if NLP.nsyl(w) >= self.thresh])


class MaxWordLengthCriteria(Criteria):
    def __init__(self, allow_used=False, thresh=6):
        self.thresh = thresh
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        return np.asarray([w for w in candidates if len(w) <= self.thresh])

class MinWordLengthCriteria(Criteria):
    def __init__(self, allow_used=False, thresh=6):
        self.thresh = thresh
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        return np.asarray([w for w in candidates if len(w) >= self.thresh])


class MinDistanceCriteria(Criteria):
    def __init__(self, distance_matrix, allow_used=False, thresh=0.0):
        self.thresh = thresh 
        self.distance_matrix = distance_matrix
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        if len(partial_list) == 0:
            return candidates

        mat_subset = self.distance_matrix.loc[partial_list, candidates]
        return mat_subset.loc[:, mat_subset.min(axis=0) >= self.thresh].columns.to_numpy()


class UniqueLettersCriteria(Criteria):
    def __init__(self, allow_used=False):
        self.allow_used = allow_used

    def filter(self, partial_list, unused, used):
        if self.allow_used:
            candidates = np.concatenate((unused, used))
        else:
            candidates = unused

        existing = {w[0] for w in partial_list}
        return np.asarray([w for w in candidates if w[0] not in existing]) 


class NoRepeatCriteria(Criteria):
    def __init__(self):
        pass

    def filter(self, partial_list, unused, used):
        return np.asarray([w for w in unused if w not in partial_list])


class SolutionFailedException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

class ListGenerator(object):
    def __init__(self, corpus, _filter, timeout=10):
        self.corpus = np.asarray(corpus)
        self.unused = self.corpus
        self.used = []
        self.timeout = timeout
        
        self.filter = _filter 

    def reset(self):
        self.used = []
        self.unused = self.corpus

    # generate n lists
    def generate_list(self, length):
        if(len(self.unused) < length):
            raise Exception("Not enough remaining words")

        # create list and grab first element
        for i in range(self.timeout):
            partial_list = []
            solved = False
            try:
                while len(partial_list) < length:
                    candidates = self.filter(partial_list, self.unused, self.used)

                    if len(candidates) == 0:
                        raise SolutionFailedException("Solution failed")

                    choice = np.random.choice(candidates)
                    partial_list.append(choice)
                solved = True
                break

            except SolutionFailedException:
                continue

        if not solved:
            raise SolutionFailedException("Solution failed")

        self.used.extend(partial_list)
        self.unused = self.corpus[~np.isin(self.corpus, self.used)]

        return np.asarray(partial_list)


class SessionGenerator(object):

    # composes list generator
    def __init__(self, list_gen, lists, reps, timeout=100, var="pregenerated_lists", **kwargs):
        self.timeout = timeout
        self.lists = lists
        self.reps = reps # last term in lists * conditions * reps
        self.list_gen = list_gen
        self.conditions = kwargs
        self.var = var


    class Session(object):
        def __init__(self, lists, conditions, labels, var='pregenerated_lists'):
            self.lists = lists
            self.conditions = conditions
            self.labels = labels
            self.var = var

        @property
        def js_string(self):

            js_string = 'var ' + self.var + ' = [\n'
            for l, c in zip(self.lists, self.conditions):
                condition_string = "conditions: {" \
                                        + ", ".join(["{}: \"{}\"".format(label, cond) for label, cond in zip(self.labels, c)]) \
                                        + "}"
                list_string = "words: [\"" + "\", \"".join(l) + "\"]"
                js_string = js_string + "\t{\n\t\t" + condition_string + ",\n\t\t" + list_string + "\n\t},\n"

            js_string = js_string + "]"

            return js_string

        @property 
        def python_string(self):
            pass

        def shuffle_lists(self):
            conditions_lists = zip(self.conditions, self.lists)
            shuffle(conditions_lists)
            conditions, lists = zip(*conditions_lists)

            self.conditions = conditions
            self.lists = lists

        def shuffle_words(self):
            pass


    def generate_conditions(self, **kwargs):
        conditions = []
        keys = list(kwargs.keys())
        for key in keys:
            if not isinstance(kwargs[key], Iterable):
                raise Exception("Each condition must be a collection that " +
                                 "can be iterated over.")

            conditions.append(kwargs[key])

        conditions = list(product(*conditions))
        return keys, conditions

    def generate_session(self):
        '''
        Need to find all long lists first for solution stability, so this is a special case
        '''

        labels, conditions = self.generate_conditions(**self.conditions)
        lists_conditions = list(product(self.lists, conditions)) 

        self.list_gen.reset()
        session = []

        for i in range(self.timeout):
            solved = False

            try:
                for reps in range(self.reps):
                    shuffle(lists_conditions)
                    for list_length, cond in lists_conditions: 
                        session.append((cond, self.list_gen.generate_list(list_length))) 
                solved = True 
                break

            except:
                self.list_gen.reset()
                session = []

        if not solved:
            raise SolutionFailedException("failed to generate list after {} iterations".format(self.timeout))

        shuffled_conditions, lists = zip(*session)

        return self.Session(lists, shuffled_conditions, labels, var=self.var)


def save_list(experiment, condition, id, session, practice=None, format="js"):
    filename = "./{}/{}/{}.js".format(experiment, condition, id)

    if format == "js":
        with open(filename, "w") as f:
            if practice is not None:
                f.writelines(practice.js_string)
                f.write("\n\n")

            f.writelines(session.js_string)

# TODO: load most recent distance matrix
