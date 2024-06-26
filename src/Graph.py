from enum import Enum, auto
import pandas as pd
import copy
import networkx as nx
import matplotlib.pyplot as plt
import itertools as it
import math
import argparse
import time

class EdgeType(Enum):
    PO = auto()
    RF = auto()
    HB = auto()
    CONC = auto()

# Taken from c11tester
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
    # TODO: Type does not checkout for HB as it can go to multiple
    edges: dict[EdgeType, dict[int,set[int]]] = {}

    def __init__(self, nodes, rawDataPath):
        self.nodes: dict[int, Node] = nodes
        self.rawData = pd.read_csv(rawDataPath)
        self.traceHasDataRace = self.rawData.iloc[-1]["data_race"]
        print("Data race in trace:",self.traceHasDataRace)
        self.rawData = self.rawData[:-1]
        self.rawData["#"] = self.rawData["#"].astype(int)

        self.edges = {EdgeType.PO: {}, EdgeType.RF: {}, EdgeType.HB: {}, EdgeType.CONC: {}}
        self.add_nodes(self.rawData)
        self.init_edges(self.rawData)
    
    def init_edges(self, graphDF):
        self.add_po_edges()
        self.add_rf_locks(graphDF)
        self.add_hb_edges()
        self.add_conc_edges()

    def add_nodes(self,graphDF):
        #print(graphDF)
        for index, row in graphDF.iterrows():
            self.nodes[row["#"]] = Node(row["#"],{},NodeType.from_string(row["action_type"]),row["location"],row["t"],row["value"],row["mo"])
            if row["rf"] != "?":
                id = int(row["rf"])
                if id not in self.edges[EdgeType.RF].keys():
                    self.edges[EdgeType.RF][id] = set()
                self.edges[EdgeType.RF][id].add(int(row["#"]))

    def add_rf_locks(self, graphDF):
        lockDF = graphDF[(graphDF["action_type"] == NodeType.ATOMIC_LOCK.value) | (graphDF["action_type"] == NodeType.ATOMIC_UNLOCK.value)][["#", "action_type", "location"]]
        lock_actions = lockDF.to_dict('records')
        for i, node in enumerate(lock_actions):
            if node["action_type"] == NodeType.ATOMIC_UNLOCK.value:
                for j in range(i+1,len(lock_actions)):
                    if lock_actions[j]["action_type"] == NodeType.ATOMIC_LOCK.value and (
                            lock_actions[i]["location"] == lock_actions[j]["location"]):
                        if lock_actions[i]["#"] not in self.edges[EdgeType.RF]:
                            self.edges[EdgeType.RF][lock_actions[i]["#"]] = set()
                        self.edges[EdgeType.RF][lock_actions[i]["#"]].add(lock_actions[j]["#"])
                        break

    def add_po_edges(self):
        # add
        self.edges[EdgeType.PO] = self.thread_splits()
        for node_no in self.nodes.keys():
            current_node = self.nodes[node_no]

            # iterate throught the remaining nodes
            # to find the next node in the same thread
            keys = list(self.nodes.keys())
            for next_node_id in keys[node_no:]:
                next_node = self.nodes[next_node_id]
                
                # Found next edge in the same thread.
                # Create and add new edge
                if next_node.t_id == current_node.t_id:
                    if current_node.id not in self.edges[EdgeType.PO].keys():
                        self.edges[EdgeType.PO][current_node.id] = set()
                    self.edges[EdgeType.PO][current_node.id].add(next_node.id)
                    break

    def thread_splits(self):
        splits = {}
        for node_no in self.nodes.keys():
            node = self.nodes[node_no]
            if node.action_type == NodeType.PTHREAD_CREATE:
                for prev_node_no in range(node_no, len(self.nodes)):
                    if self.nodes[prev_node_no].action_type == NodeType.THREAD_START:
                        splits[node_no] = {prev_node_no}
                        break
        return splits

    def add_hb_edges(self):
        for id in self.nodes.keys():
            if id in self.edges[EdgeType.PO].keys():
                destination_ids = self.edges[EdgeType.PO][id]
                for destination_id in destination_ids:
                    
                    # remove self loops
                    if destination_id == id:
                        continue

                    if id not in self.edges[EdgeType.HB].keys():
                        self.edges[EdgeType.HB][id] = set()
                    self.edges[EdgeType.HB][id].add(destination_id)

            if id in self.edges[EdgeType.RF].keys():
                destination_ids = self.edges[EdgeType.RF][id]
                for destination_id in destination_ids:
                    if id not in self.edges[EdgeType.HB].keys():
                        self.edges[EdgeType.HB][id] = set()
                    self.edges[EdgeType.HB][id].add(destination_id)
                    # print(self.edges[EdgeType.HB][id])

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
            if src_node_id not in self.edges[EdgeType.CONC].keys():
                self.edges[EdgeType.CONC][src_node_id] = set()
            for dest_node_id in self.nodes.keys():
                if dest_node_id not in self.edges[EdgeType.CONC].keys():
                    self.edges[EdgeType.CONC][dest_node_id] = set()
                if src_node_id == dest_node_id:
                    continue
                if ((src_node_id not in self.edges[EdgeType.HB]) or (dest_node_id not in self.edges[EdgeType.HB][src_node_id])) and (
                        (dest_node_id not in self.edges[EdgeType.HB]) or (src_node_id not in self.edges[EdgeType.HB][dest_node_id])
                        ):
                    self.edges[EdgeType.CONC][src_node_id].add(dest_node_id)
                    self.edges[EdgeType.CONC][dest_node_id].add(src_node_id)
    def find_data_races(self):
        race_count = 0
        races = {}
        read_actions = [NodeType.ATOMIC_READ, NodeType.ATOMIC_RMW]
        write_actions = [NodeType.ATOMIC_WRITE, NodeType.ATOMIC_RMW]
        accepted_actions = read_actions + write_actions
        for src_node_id,dest_nodes in self.edges[EdgeType.CONC].items():
            # Ignore edges that are both sequentially consistent
            for dest_node_id in dest_nodes:
                # Avoid being redundant
                if dest_node_id <= src_node_id:
                    continue
                if self.nodes[src_node_id].mo == "seq_cst" and self.nodes[dest_node_id].mo == "seq_cst":
                    continue
                if self.nodes[src_node_id].action_type not in accepted_actions:
                    continue
                if self.nodes[dest_node_id].action_type not in accepted_actions:
                    continue
                if self.nodes[dest_node_id].mem_loc != self.nodes[src_node_id].mem_loc:
                    continue
                if self.nodes[src_node_id].action_type in write_actions or self.nodes[dest_node_id].action_type in write_actions:
                    print("Data race found between: ", src_node_id, dest_node_id)
                    race_count+=1
                    races[src_node_id] = dest_node_id
        print("Total data races found: ", race_count)

    #Draw the first nnodes nodes and show rf and po relations
    def visualize(self, nnodes):
        G = nx.MultiDiGraph()
        G.add_nodes_from(self.nodes.keys())
        rf_edges = []
        for src, dsts in self.edges[EdgeType.RF].items():
            for dst in dsts:
                rf_edges.append((src, dst))
        G.add_edges_from(rf_edges, label="RF", color="green")
        po_edges = []
        for src, dsts in self.edges[EdgeType.PO].items():
            for dst in dsts:
                po_edges.append((src, dst))
        G.add_edges_from(po_edges, label="PO", color="black")
        G.remove_nodes_from([i for i in range(nnodes+1,len(self.nodes)+1)])
        connectionstyle = [f"arc3,rad={r}" for r in it.accumulate([0.15] * 4)]

        pos = nx.spring_layout(G, k=5/math.sqrt(len(G.nodes)))
        nx.draw_networkx_nodes(G, pos)
        nx.draw_networkx_labels(G, pos, font_size=12)
        colors = nx.get_edge_attributes(G, "color").values()
        nx.draw_networkx_edges(
            G, pos, edge_color=colors, connectionstyle=connectionstyle
        )
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog="Graph.py",
            description="Build a graph and detects RA-dataraces from a c11tester trace")
    parser.add_argument("-d", "--draw", type=int, nargs=1)
    parser.add_argument("-i", "--input",type=str, help="Path to the input trace", required=True)
    start_time = time.time()
    args = parser.parse_args()
    graph = Graph({},args.input)
    graph.find_data_races()
    print("Elapsed time:", time.time() - start_time)
    if args.draw != None:
        graph.visualize(args.draw[0])
