from ..utils import progress_bar, strip_tags, change_key, filter_keys
# since jspsych is organized around plugins, we can break plugin processing
# from event creation code into a single function per plugin type, that can 
# then be used to create events

# TODO: change to filtering out unwated keys, as experiments may add their own
# data to the node that we want to pick up, but unwanted keys should be constant
# (ie trial index)

#audio-keyboard-response
def audio_keyboard_response_node(trialdata):
    # TODO: flip to unwanted keys
    wanted_keys = ["block", "length", "pr", "conditions"]

    event = {}

    event = filter_keys(wanted_keys, trialdata)
    event['phase'] = trialdata['phase']
    event['listtype'] = trialdata['listtype']
    event["mstime"] = trialdata["time_elapsed"]
    event["type"] = "WORD"
    item = strip_tags(trialdata["stimulus"])
    item = item.strip('/static/sound/')
    item = item.strip('.wav')
    event['item'] = item

    return (event, )

#html-keyboard-response
def html_keyboard_response_node(trialdata):
    # TODO: flip to unwanted keys
    wanted_keys = ["block", "length", "pr", "conditions"]

    event = {}

    event = filter_keys(wanted_keys, trialdata)
    event['phase'] = trialdata['phase']
    event["mstime"] = trialdata["time_elapsed"]
    event["type"] = "WORD"
    event["item"] = strip_tags(trialdata["stimulus"])

    return (event, )


#hold-keys
def hold_keys_node(trialdata):
    base_event, *_ = html_keyboard_response_node(trialdata)
    base_event["held_over"] = trialdata["held_over"]

    base_event["key_up"] = trialdata["key_up"]
    base_event["key_down"] = trialdata["key_down"]

    base_event["rt_up"] = trialdata["rt_up"]
    base_event["rt_down"] = trialdata["rt_down"]

    return (base_event, )


#hold-keys-check
def hold_keys_check_node(trialdata):
    event = {}
    event["held_over"] = trialdata["held_over"]
    event["all_down"]  = trialdata["all_down"]
    event["to_hold"]   = trialdata["to_hold"]

    return (event, )


#free-recall
def free_recall_node(trialdata):

    recwords = trialdata["recwords"] 
    rts = trialdata["rt"]

    if len(recwords) == 0:
        rts = [0]
        recwords = [""]
    
    time = trialdata["start_time"]

    events = []

    event = {}
    event["type"] = "START_RECALL"
    event["mstime"] = time
    event["phase"] = trialdata.get('phase')
    event['recall type'] = trialdata['recall_type']
    event["listtype"] = trialdata.get('listtype')
    events.append(event)

    for w, t in zip(recwords, rts):
        event = {}

        event["mstime"] = time + t
        event["phase"] = trialdata.get('phase')
        event['recall type'] = trialdata['recall_type']
        event["listtype"] = trialdata.get('listtype')
        event["rt"] = t
        event["type"] = "REC_WORD"
        event["item"] = w.upper() 
        event["conditions"] = trialdata.get("conditions", None)

        events.append(event)

    event = {}
    event["type"] = "END_RECALL"
    event["mstime"] = trialdata["time_elapsed"]
    event["phase"] = trialdata.get('phase')
    event['recall type'] = trialdata['recall_type']
    event["listtype"] = trialdata.get('listtype')
    events.append(event)
    
    return events


#free-sort
def free_sort_node(trialdata):
    events = []
    wanted_keys = ["block", "length", "pr", "conditions"]

    start_time = trialdata["start_time"]

    event = filter_keys(wanted_keys, trialdata)
    event["type"] = "START_RECALL"
    event["mstime"] = start_time
    events.append(event)

    for d_ev in trialdata["drag_events"]:

        event = filter_keys(wanted_keys, trialdata)
        event["mstime"] = start_time + d_ev["time"]
        event["type"] = "DRAG"
        event["mode"] = d_ev["mode"]
        event["rt"] = d_ev["time"]
        event["item"] = strip_tags(d_ev["word"])
        event["target"] = d_ev["target"]
        event["conditions"] = trialdata.get("conditions", None)

        events.append(event)

    event = filter_keys(wanted_keys, trialdata)
    event["mstime"] = trialdata["time_elapsed"]

    # start postitions are position on recall screen, not at encoding
    event["start_positions"] = [strip_tags(w) for w in trialdata["original_wordorder"]] 
    event["end_positions"]   = [strip_tags(w) for w in trialdata["final_wordorder"]]
    event["type"] = "END_RECALL"
    event["conditions"] = trialdata.get("conditions", None)
    events.append(event)

    return events


#positional-html-display
def positional_html_display_node(trialdata):
    base_event, *_ = hold_keys_node(trialdata)
    base_event["position"] = (trialdata["row"], trialdata["col"]) 
    base_event["grid_size"] = (trialdata["grid_rows"], trialdata["grid_cols"]) 
    base_event["conditions"] = trialdata.get("conditions", None)

    return (base_event, )


#math-distractor
def math_distractor_node(trialdata):
    wanted_keys = ["rt", "responses", "num1", "num2", "num3"]

    event = filter_keys(wanted_keys, trialdata)
    event["mstime"] = trialdata["time_elapsed"]
    event["type"] = "DISTRACTOR"
    event["conditions"] = trialdata.get("conditions", None)

    return (event, )

def countdown_node(trialdata):
    event = {} 
    event["mstime"] = trialdata["time_elapsed"]
    event["type"] = "COUNTDOWN"

    return (event, )
