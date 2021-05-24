import json
from post_process.data_container import DataContainer

data_dict = {"root": "/data/behavioral/mturk",
             "experiment": "serial_recall_2"}
subs = DataContainer(**data_dict).get_raw_data()

for sub in subs:
    try:
        b = sub["datastring"]["condition"]
    except:
        try:
            json.loads(sub["datastring"])
        except Exception as e:
            print(e)
            print(sub["workerid"])
            import pdb; pdb.set_trace()
