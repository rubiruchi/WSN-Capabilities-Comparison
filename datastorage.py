from collections import OrderedDict
from copy import deepcopy

class DataStorage:
    top_store = None #list of functions
    dict_platforms_to_listchan = None
    list_channels_with_dictparam = None
    dict_parameters_to_txval = None

    txpowers = {}
    indices = OrderedDict()
    functions = []


    def __init__(self):
        self.txpowers["openmote-cc2538"] = [5,3,1,0,-1,-3,-5,-7,-15]
        self.txpowers["srf06-cc26xx"] = [5,3,1,0,-3,-15]
        self.txpowers["z1"] = [0,-1,-3,-5,-7,-15]
        self.txpowers["sky"] = [0,-1,-3,-5,-7,-15]
        self.indices["0"] = 0 #RSSI
        self.indices["1"] = 1 #LQI
        self.indices["2"] = 2 #DROPPED
        self.indices["time"] = 3
        self.indices["lines"] = 4
        self.indices["size"] = 5
        self.indices["failed"] = 6
        self.indices["packetlossrate"] = 7
        self.functions = ["avg","dev","min","max"]

        self.top_store = {}
        self.dict_function_to_platform = {}
        self.dict_platforms_to_listchan = {}
        self.list_channels_with_dictparam = []
        self.dict_parameters_to_txval = {}

        #init dict: parameters to tuple
        for parameter in self.indices.keys():
            self.dict_parameters_to_txval[parameter] = ([],[])

        #init dict: channels to (dict parameters to tuple)
        for i in range(11,27):
            self.list_channels_with_dictparam.append(deepcopy(self.dict_parameters_to_txval))

        #init dict platforms to (dict channels to (dict parameters to tuple))
        for platform in self.txpowers.keys():
            self.dict_platforms_to_listchan[platform] = deepcopy(self.list_channels_with_dictparam)

        # ...
        for function in self.functions:
            self.top_store[function] = deepcopy(self.dict_platforms_to_listchan)


    def store(self, info, value, txpower = None, tx_val = None):
        function = info["function"]
        platform = info["platform"]
        channel =  int(info["channel"])-11
        parameter = info["parameter"]

        if tx_val:
            if isinstance(tx_val,tuple):
                self.top_store[function][platform][channel][parameter] = tx_val
            else:
                raise Exception("trying to set txval to something that is not a tuple")

        if not txpower is None:
            self.top_store[function][platform][channel][parameter][0].append(txpower)
            self.top_store[function][platform][channel][parameter][1].append(value)


    def get(self,function = None, platform = None, channel = None, parameter = None):
        if channel:
            channel = int(channel)-11

        if parameter:
            return self.top_store[function][platform][channel][parameter]
        elif channel:
            return self.top_store[function][platform][channel]
        elif platform:
            return self.top_store[function][platform]
        elif function:
            return self.top_store[function]
