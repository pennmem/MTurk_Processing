from .presrate_cleaner import PresRateCleaner
from .serialrec_cleaner import SerialRecCleaner
from .orderedrecall_cleaner import OrderedRecallCleaner
from .repfr_cleaner import RepFRCleaner


def get_cleaner(data_container):
    if data_container.experiment == "NFA":
        raise Exception("Experiment Not Supported")

    elif data_container.experiment == "serial_recall_2":
        return SerialRecCleaner(data_container) 

    elif data_container.experiment == "presrate":
        return PresRateCleaner(data_container)

    elif data_container.experiment == "ordered_recall":
        return OrderedRecallCleaner(data_container)

    elif data_container.experiment == "repFR":
        return RepFRCleaner(data_container)

    raise Exception("Experiment Not Supported")
