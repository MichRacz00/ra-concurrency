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

class Node:
    id = -1
    action_type = NodeType.ATOMIC_INIT
    mem_loc = -1
    t_id = -1
    value = -1

    def __init__(self, node_id, node_edges, action_type, mem_loc, thread_id, value):
        self.id = node_id
        self.edges = node_edges
        self.action_type = action_type
        self.mem_loc = mem_loc
        self.t_id = thread_id
        self.value = value

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
        self.add_nodes(self.rawData)
        self.edges = {EdgeType.PO: {}, EdgeType.MO: {}, EdgeType.RF: {}, EdgeType.FR: {}, EdgeType.HB: {}}
        
    def add_nodes(self,graphDF):
        #print(graphDF)
        for index, row in graphDF.iterrows():
            #print(Node(row["#"],{},row["action_type"],row["location"],row["t"]))
            self.nodes[row["#"]] = Node(row["#"],{},NodeType.from_string(row["action_type"]),row["location"],row["t"],row["value"])
        

    def add_po_edges(self):
        edges = []
        splits = self.thread_splits()

        for node_no in self.nodes.keys():
            current_node = self.nodes[node_no]

            # iterate throught the remaining nodes
            # to find the next node in the same thread
            keys = list(self.nodes.keys())
            for next_node_id in keys[node_no:]:
                next_node = self.nodes[next_node_id]

                # this is the first event in the thread,
                

                # Found next edge in the same thread.
                # Create and add new edge
                if next_node.t_id == current_node.t_id:
                    self.edges[EdgeType.PO][current_node.id] = next_node.id
                    #current_node.edges.append(new_po_edge)
                    #print(current_node.id, next_node.id)
                    break

        #print(edges)

    # Binds values to threads ids to track thread splits.
    # Creates dictionary indexed with value of thread split
    # event. Dictionary contains t_id and number of threads created.
    def thread_splits(self):
        splits = {}
        for node_no in self.nodes.keys():
            node = self.nodes[node_no]

            if node.action_type == NodeType.THREAD_START.value:
                if node.value not in splits.keys():
                    splits[node.value] = {"t_id": 0, "t_num": 0}
                else:
                    splits[node.value]["t_num"] += 1
        return splits

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
            self.edges[EdgeType.MO][prevIndex] = row['#']
            prevIndex = row['#']
            print(prevIndex)
    
    def add_rf_edges(self):
        for read_id, read_node in self.nodes.items():
            if not (read_node.action_type == NodeType.ATOMIC_READ or read_node.action_type == NodeType.ATOMIC_RMW):
                continue
            #find last write w
            #add edge (w, id)
            curr_id = read_id - 1
            while True:
                if curr_id == 0:
                    raise Exception(f"No write found for read id {read_id}")
                curr_node = self.nodes[curr_id]
                if (curr_node.action_type == NodeType.ATOMIC_WRITE or 
                        curr_node.action_type == NodeType.ATOMIC_RMW) and curr_node.mem_loc == read_node.mem_loc:
                    self.edges[EdgeType.RF][curr_id] = read_id
                    break
                curr_id -= 1

    def add_fr_edges(self):
        pass

    def add_hb_edges(self):
        pass

    def has_data_races():
        pass


graph = Graph({},"../data_race.csv")
print(len(graph.nodes))
graph.add_mo_edges()
graph.add_rf_edges()
for node in graph.nodes:
    print(graph.nodes[node])
