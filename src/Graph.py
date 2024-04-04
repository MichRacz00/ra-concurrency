from enum import Enum, auto
import pandas as pd
import copy

class EdgeType(Enum):
    MO = auto()
    PO = auto()
    RF = auto()
    FR = auto()
    HB = auto()
    CONC = auto()

class NodeType(Enum):
    THREAD_CREATE = "thread create"
    THREAD_START = "thread start"
    THREAD_YIELD = "thread yield"
    THREAD_JOIN = "thread join"
    THREAD_FINISH = "thread finish"
    THREAD_SLEEP = "thread sleep"
    THREADONLY_FINISH = "pthread_exit finish"
    PTHREAD_CREATE = "pthread create"
    PTHREAD_JOIN = "pthread join"
    NONATOMIC_WRITE = "nonatomic write"
    ATOMIC_READ = "atomic read"
    ATOMIC_WRITE = "atomic write"
    ATOMIC_RMW = "atomic rmw"
    ATOMIC_FENCE = "fence"
    ATOMIC_RMWR = "atomic rmwr"
    ATOMIC_RMWRCAS = "atomic rmwrcas"
    ATOMIC_RMWC = "atomic rmwc"
    ATOMIC_INIT = "init atomic"
    ATOMIC_LOCK = "lock"
    ATOMIC_UNLOCK = "unlock"
    ATOMIC_TRYLOCK = "trylock"
    ATOMIC_WAIT = "wait"
    ATOMIC_TIMEDWAIT = "timed wait"
    ATOMIC_NOTIFY_ONE = "notify one"
    ATOMIC_NOTIFY_ALL = "notify all"
    ATOMIC_ANNOTATION = "annotation"


    def from_string(value):
        for member in NodeType:
            if member.value == value:
                return member
        raise ValueError(f'{value} is not a valid NodeType value')

class Node:
    id = -1
    action_type = NodeType.ATOMIC_INIT
    mem_loc = -1
    t_id = -1
    value = -1
    mo = None

    def __init__(self, node_id, node_edges, action_type, mem_loc, thread_id, value, mo):
        self.id = node_id
        self.edges = node_edges
        self.action_type = action_type
        self.mem_loc = mem_loc
        self.t_id = thread_id
        self.value = value
        self.mo = mo

    def __str__(self):
        return f'Node(id={self.id}, mem_loc={self.mem_loc}, t_id={self.t_id}, type={self.action_type}, value={self.value})'

class Graph:
    nodes = {}
    rawData = None
    # Dict of all edges in graph edgetype->dict[in -> out]
    edges: dict[EdgeType, dict[int, int]] = {}

    def __init__(self, nodes, rawDataPath):
        self.nodes: dict[int, Node] = nodes
        self.rawData = pd.read_csv(rawDataPath)
        self.edges = {EdgeType.PO: {}, EdgeType.MO: {}, EdgeType.RF: {}, EdgeType.FR: {}, EdgeType.HB: {}, EdgeType.CONC: {}}
        self.add_nodes(self.rawData)
        self.init_edges()
    
    def init_edges(self):
        self.add_po_edges()
        self.add_mo_edges()
        self.add_fr_edges()
        self.add_hb_edges()
        self.add_conc_edges()

    def add_nodes(self,graphDF):
        #print(graphDF)
        for index, row in graphDF.iterrows():
            self.nodes[row["#"]] = Node(row["#"],{},NodeType.from_string(row["action_type"]),row["location"],row["t"],row["value"],row["mo"])
            if row["rf"] != "?":
                self.edges[EdgeType.RF][row["#"]] = int(row["rf"])  

    def add_po_edges(self):
        edges = []
        splits = self.thread_splits()
        for node_no in self.nodes.keys():
            current_node = self.nodes[node_no]

            # this is the first event in the thread
            if current_node.action_type == NodeType.THREAD_START:
                split = splits[current_node.value]

                # assuming thread start is in the previous instruction
                origin_id = split["origins"].pop() - 1
                if origin_id > 0:
                    origin_node = self.nodes[origin_id]
                    self.edges[EdgeType.PO][origin_node.id] = current_node.id
                    #print(origin_id, current_node.id)

            # iterate throught the remaining nodes
            # to find the next node in the same thread
            keys = list(self.nodes.keys())
            for next_node_id in keys[node_no:]:
                next_node = self.nodes[next_node_id]
                
                # Found next edge in the same thread.
                # Create and add new edge
                if next_node.t_id == current_node.t_id:
                    self.edges[EdgeType.PO][current_node.id] = next_node.id
                    break  

    # Binds values to threads ids to track thread splits.
    # Creates dictionary indexed with value of thread split
    # event. Dictionary contains t_id and number of threads created.
    def thread_splits(self):
        splits = {}
        for node_no in self.nodes.keys():
            node = self.nodes[node_no]

            if node.action_type == NodeType.THREAD_START:
                if node.value not in splits.keys():
                    splits[node.value] = {"origins": [node.id], "t_num": node.t_id}
                else:
                    splits[node.value]["origins"] = [node.id] + splits[node.value]["origins"]
        return splits

    def add_mo_edges(self):
        filtered_df = self.rawData[self.rawData['action_type'].isin([NodeType.ATOMIC_WRITE.value, NodeType.ATOMIC_RMW.value])]
        prevIndex = -1
        for index, row in filtered_df.iterrows():
            if prevIndex == -1:
                prevIndex = row['#']
                continue

            if not row['#'] in self.nodes[prevIndex].edges:
                self.nodes[prevIndex].edges[row['#']] = {}
            self.edges[EdgeType.MO][prevIndex] = row['#']
            prevIndex = row['#']

    def add_fr_edges(self):
        for id in self.nodes.keys():
            if id in self.edges[EdgeType.RF] and id in self.edges[EdgeType.MO]:
                self.edges[EdgeType.FR][self.edges[EdgeType.RF][id]] = self.edges[EdgeType.MO][id]

    def add_hb_edges(self):
        for id in self.nodes.keys():
            if id in self.edges[EdgeType.PO].keys():
                destination_id = self.edges[EdgeType.PO][id]
                if destination_id not in self.edges[EdgeType.HB].keys():
                    self.edges[EdgeType.HB][id] = set()
                self.edges[EdgeType.HB][id].add(destination_id)

            if id in self.edges[EdgeType.RF].keys():
                destination_id = self.edges[EdgeType.RF][id]
                if destination_id not in self.edges[EdgeType.HB].keys():
                    self.edges[EdgeType.HB][id] = set()
                self.edges[EdgeType.HB][id].add(destination_id)

        self.__hb_transitive()

    def __hb_transitive(self):
        # Iterate untill no new relations are added
        while True:
            # Keep a copy of HB relation to see if new relations were added
            hb_relation_copy = copy.deepcopy(self.edges[EdgeType.HB])

            # Initialize a dictionary to collect the transitive relation
            transitive = {}

            for origin_id, destination_ids in self.edges[EdgeType.HB].items():
                # Iterate over a copy of the set to not alter it in the loop
                for destination_id in destination_ids.copy():
                    if destination_id in self.edges[EdgeType.HB]:
                        next_destination_ids = self.edges[EdgeType.HB][destination_id]
                        transitive.setdefault(origin_id, set()).update(next_destination_ids)

            # Merge collected transitive relation
            for origin_id, next_destination_ids in transitive.items():
                self.edges[EdgeType.HB][origin_id].update(next_destination_ids)

            # If no new relations were added, transitive property was exhausted
            if self.edges[EdgeType.HB] == hb_relation_copy:
                return
    # Edges without HB relation
    def add_conc_edges(self):
        for src_node_id in self.nodes.keys():
            self.edges[EdgeType.CONC][src_node_id] = set()
            for dest_node_id in self.nodes.keys():
                if not src_node_id in self.edges[EdgeType.HB] or not dest_node_id in self.edges[EdgeType.HB][src_node_id]:
                    self.edges[EdgeType.CONC][src_node_id].add(dest_node_id)
        

    def find_data_races(self):
        race_count = 0
        races = {}
        read_actions = [NodeType.ATOMIC_READ]
        write_actions = [NodeType.ATOMIC_WRITE]
        accepted_actions = read_actions + write_actions
        for src_node_id,dest_nodes in self.edges[EdgeType.CONC].items():
            # Ignore edges that are both sequentially consistent
            for dest_node_id in dest_nodes:
                # Avoid being redundant
                if dest_node_id <= src_node_id:
                    continue
                if self.nodes[src_node_id].mo == "seq_qst" and self.nodes[dest_node_id].mo == "seq_const":
                    continue
                if self.nodes[src_node_id].action_type not in accepted_actions:
                    continue
                if self.nodes[dest_node_id].action_type not in accepted_actions:
                    continue
                if self.nodes[src_node_id].action_type in write_actions or self.nodes[dest_node_id].action_type in write_actions:
                    print("Data race found between: ", src_node_id, dest_node_id)
                    race_count+=1
                    races[src_node_id] = dest_node_id
        print("Total data races found: ", race_count)


graph = Graph({},"../presentation_trace.csv")
graph.find_data_races()
