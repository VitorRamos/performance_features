import perfmon

class ListEvents:
    def __init__(self):
        self.system = perfmon.System()

    def get_supported_pmus(self):
            pmus= []
            for pmu in self.system.pmus:
                pmu_info= pmu.info
                if pmu_info.flags.is_present:
                    pmus.append(pmu_info.name)
            return pmus

    def get_supported_events(self, name=''):
        evs= []
        for pmu in self.system.pmus:
            pmu_info= pmu.info
            if pmu_info.flags.is_present:
                for event in pmu.events():
                    if name in event.info.name:
                        evs.append(event.info.name)
        return evs
    
    def get_event_attrs(self, name):
        attrs=[]
        for pmu in self.system.pmus:
            pmu_info= pmu.info
            if pmu_info.flags.is_present:
                for event in pmu.events():
                    if name in event.info.name:
                        for att in event.attrs():
                            attrs.append([att.name,att.desc])
        return attrs

    def get_event_description(self, name=''):
        evs= []
        for pmu in self.system.pmus:
            pmu_info= pmu.info
            if pmu_info.flags.is_present:
                for event in pmu.events():
                    if name in event.info.name:
                        evs.append([event.info.name,event.info.desc])
        return evs