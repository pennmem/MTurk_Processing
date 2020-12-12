from .serialrec_report import SerialRecallReport
from .ordered_recall_report import OrderedRecallReport
from .repfr_report import RepFRReport

def get_reporter(data_container):
    if data_container.experiment == "serial_recall_2":
        return SerialRecallReport(data_container)

    if data_container.experiment == "ordered_recall":
        return OrderedRecallReport(data_container)

    if data_container.experiment == "repFR":
        return RepFRReport(data_container)

    raise Exception(f"Experiment {data_container.experiment} Not Supported")
