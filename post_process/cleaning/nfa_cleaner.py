from .experiment_cleaning import DataCleaner

class NFACleaner(DataCleaner):
    def __init__(self, data_container):
        super().__init__(data_container)

    def clean(self, force=False, verbose=False):
        self.process_survey()
