# from cleaning.nfa_cleaner import NFACleaner
# from .cleaning.presrate_cleaner import PresRateCleaner
# from .cleaning.serialrec_cleaner import SerialRecCleaner
# from .cleaning.orderedrecall_cleaner import OrderedRecallCleaner
# from .cleaning.repfr_cleaner import RepFRCleaner
from .cleaning.cvltdfr_cleaner import CVLTDFRCleaner 
from .cleaning.cvlt_cleaner import CVLTCleaner 
from .cleaning.fr1_cleaner import FR1Cleaner 



class CleanerFactory(object):
    @staticmethod
    def get_cleaner(data_container):
        if data_container.experiment == "NFA":
            raise Exception("Experiment Not Supported")
            # return NFACleaner(data_container)

        # elif data_container.experiment == "serial_recall_2":
        #     return SerialRecCleaner(data_container) 

        # elif data_container.experiment == "presrate":
        #     return PresRateCleaner(data_container)

        # elif data_container.experiment == "ordered_recall":
        #     return OrderedRecallCleaner(data_container)

        # elif data_container.experiment == "repFR":
        #     return RepFRCleaner(data_container)
        
        elif data_container.experiment == "CVLT-DFR":
            return CVLTDFRCleaner(data_container)
        
        elif data_container.experiment == "CVLT":
            return CVLTCleaner(data_container)
        
        elif data_container.experiment == "FR1":
            return FR1Cleaner(data_container)

        raise Exception("Experiment Not Supported")
