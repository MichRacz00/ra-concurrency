from enum import Enum, auto
import pandas as pd

class EdgeType(Enum):
    MO = auto()
    PO = auto()
    RF = auto()
    FR = auto()
    HB = auto()

class NodeType(Enum):
    THREAD_CREATE = auto()
    THREAD_START = auto()
    THREAD_YIELD = auto()
    THREAD_JOIN = auto()
    THREAD_FINISH = auto()
    THREADONLY_FINISH = auto()
    THREAD_SLEEP = auto()
    PTHREAD_CREATE = auto()
    PTHREAD_JOIN = auto()
    NONATOMIC_WRITE = auto()
    ATOMIC_INIT = auto()
    ATOMIC_WRITE = auto()
    ATOMIC_RMW = auto()
    ATOMIC_READ = auto()
    ATOMIC_RMWR = auto()
    ATOMIC_RMWRCAS = auto()
    ATOMIC_RMWC = auto()
    ATOMIC_FENCE = auto()
    ATOMIC_LOCK = auto()
    ATOMIC_TRYLOCK = auto()
    ATOMIC_UNLOCK = auto()
    ATOMIC_NOTIFY_ONE = auto()
    ATOMIC_NOTIFY_ALL = auto()
    ATOMIC_WAIT = auto()
    ATOMIC_TIMEDWAIT = auto()
    ATOMIC_ANNOTATION = auto()
    READY_FREE = auto()
    ATOMIC_NOP = auto()

class Edge:
    in_node = -1
    out_node = -1
    node_type = EdgeType.PO

    def __init__(self, in_node, out_node, node_type):
        self.in_node = in_node
        self.out_node = out_node
        self.node_type = node_type

    def __str__(self):
        return f'MyClass(from={self.in_node}, to={self.out_node}, type={self.node_type})'

class Node:
    id = -1
    edges = {}
    action_type = NodeType.ATOMIC_NOP
    mem_loc = -1
    t_id = -1

    def __init__(self, node_id, node_edges, action_type, mem_loc, thread_id):
        self.id = node_id
        self.edges = node_edges
        self.action_type = action_type
        self.mem_loc = mem_loc
        self.t_id = thread_id

    def __str__(self):
        return f'MyClass(id={self.id}, mem_loc={self.mem_loc}, t_id={self.t_id}, type={self.action_type})'

class Graph:
    nodes = {}
    rawData = None

    def __init__(self, nodes, rawDataPath):
        self.nodes = nodes
        self.rawData = pd.read_csv(rawDataPath)
        self.add_nodes(self.rawData)
        
    def add_nodes(self,graphDF):
        print(graphDF)
        for index, row in graphDF.iterrows():
            print(Node(row["#"],{},row["action_type"],row["location"],row["t"]))
            self.nodes[row["#"]] = Node(row["#"],{},row["action_type"],row["location"],row["t"])

    def add_po_edges(self):
        pass

    def add_mo_edges(self):
        pass

    def add_rf_edges(self):
        pass

    def add_fr_edges(self):
        pass

    def add_hb_edges(self):
        pass

    def has_data_races():
        pass


graph = Graph({},"../data_race.csv")
print(len(graph.nodes))