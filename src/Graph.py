from enum import Enum, auto
import pandas as pd

class EdgeType(Enum):
    MO = auto()
    PO = auto()
    RF = auto()
    FR = auto()
    HB = auto()

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

class Edge:
    in_node = -1
    out_node = -1
    edge_type = EdgeType.PO

    def __init__(self, in_node, out_node, edge_type):
        self.in_node = in_node
        self.out_node = out_node
        self.edge_type = edge_type

    def __str__(self):
        return f'Edge(from={self.in_node}, to={self.out_node}, type={self.edge_type})'

class Node:
    id = -1
    edges = {} # 1 -> 2 edges[2] = Edge(1,2,type    )
    action_type = NodeType.ATOMIC_INIT
    mem_loc = -1
    t_id = -1

    def __init__(self, node_id, node_edges, action_type, mem_loc, thread_id):
        self.id = node_id
        self.edges = node_edges
        self.action_type = action_type
        self.mem_loc = mem_loc
        self.t_id = thread_id

    def __str__(self):
        return f'Node(id={self.id}, mem_loc={self.mem_loc}, t_id={self.t_id}, type={self.action_type})'

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
            self.nodes[row["#"]] = Node(row["#"],{},NodeType.from_string(row["action_type"]),row["location"],row["t"])

    def add_po_edges(self):
        pass

    def add_mo_edges(self):
        print(NodeType.ATOMIC_READ.value)
        filtered_df = self.rawData[self.rawData['action_type'].isin([NodeType.ATOMIC_WRITE.value, NodeType.ATOMIC_RMW.value])]
        prevIndex = -1
        print(filtered_df)
        for index, row in filtered_df.iterrows():
            if prevIndex == -1:
                prevIndex = row['#']
                continue

            if not row['#'] in self.nodes[prevIndex].edges:
                self.nodes[prevIndex].edges[row['#']] = {}
            self.nodes[prevIndex].edges[row['#']][EdgeType.MO] = Edge(prevIndex, row['#'], EdgeType.MO)
            prevIndex = row['#']
            print(prevIndex)
    
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
graph.add_mo_edges()
for node in graph.nodes:
    print(graph.nodes[node])