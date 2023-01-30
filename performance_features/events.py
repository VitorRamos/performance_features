import perfmon

_events_system = perfmon.System()


def get_supported_pmus():
    pmus = []
    for pmu in _events_system.pmus:
        pmu_info = pmu.info
        if pmu_info.flags.is_present:
            pmus.append(pmu_info.name)
    return pmus


def get_supported_events(name=""):
    evs = []
    for pmu in _events_system.pmus:
        pmu_info = pmu.info
        if pmu_info.flags.is_present:
            for event in pmu.events():
                if name in event.info.name:
                    evs.append(event.info.name)
    return evs


def get_event_description(name=""):
    evs = []
    for pmu in _events_system.pmus:
        pmu_info = pmu.info
        if pmu_info.flags.is_present:
            for event in pmu.events():
                if name in event.info.name:
                    evs.append([event.info.name, event.info.desc])
    return evs


def get_event_attrs(name):
    attrs = []
    for pmu in _events_system.pmus:
        pmu_info = pmu.info
        if pmu_info.flags.is_present:
            for event in pmu.events():
                if name in event.info.name:
                    for att in event.attrs():
                        attrs.append([att.name, att.desc])
    return attrs
