import random
import networkx as nx
import numpy as np
import sys
from typing import List, Dict
from networkx.algorithms import isomorphism


class Mapping:

    # mapping: List of tuples ("logical_node_string", physical_node_int)
    # physical graph = physical circuit configuration
    # logical graph = CTG
    def __init__(self):
        self.logical_graph = nx.Graph()
        self.ancilla_num = 0
        self.physical_graph = nx.Graph()
        self.map = []

    def __repr__(self):
        # list(self.logical_graph.nodes(data=True)
        return "Logical mapping:\n {} \nPhysical mapping:\n {} \nLogical to physical mapping:\n {} \n".format(
            list(self.logical_graph.edges(data=True)), list(self.physical_graph.edges()), list(self.map))

    # add nodes to the physical graph
    # Use example:
    #   set_nodes_physical([1, 2, 3])
    def set_nodes_physical(self, coupling_list: List[List[int]]):
        flat_list = [item for sublist in coupling_list for item in sublist]
        self.physical_graph.add_nodes_from(list(dict.fromkeys(flat_list)))

    # add nodes to the logical graph
    # Use example:
    #   set_nodes_logical([1, 2, 3])
    def set_nodes_logical(self, variables: List[str]):
        self.logical_graph.add_nodes_from(variables)

    # add undirected unweighted edges to the physical graph
    # uses coupling list as an argument
    def physical_add_edges(self, coupling_list: List[List[int]]):
        for item in coupling_list:
            if not self.physical_graph.has_edge(item[0], item[1]) or not self.physical_graph.has_edge(item[1], item[0]):
                self.physical_graph.add_edge(item[0], item[1])
            else:
                continue

                # plus one by default

    # adds undirected weighted edge to the logical graph if it doesn't exist
    def logical_add_weight(self, node1: str, node2: str, weight=1):
        e = (node1, node2, weight)
        if self.logical_graph.has_edge(*e[:2]):
            self.logical_graph[node1][node2]['weight'] += 1
        else:
            self.logical_graph.add_weighted_edges_from([e])   

    # returns True if physical degree is less than logical
    def physical_degree_is_less(self):
        degree_sequence = sorted([d for n, d in self.logical_graph.degree(weight="weight")], reverse=True)
        max_logical_degree = max(degree_sequence)
        degree_sequence = sorted([d for n, d in self.physical_graph.degree()], reverse=True)
        max_physical_degree = max(degree_sequence)

        if (max_physical_degree < max_logical_degree):
            return True
        else:
            return False

    # returns the mapping from logical to physical qubits
    def get_mapping(self):
        variable_mapping = []
        ancilla_mapping = []
        for (k, v) in self.map:
            if k.startswith('ancilla'):
                ancilla_mapping.append((k, v))
            else:
                variable_mapping.append((k, v))
        return variable_mapping, ancilla_mapping

    # returns the list of physical qubits used
    def get_physical_qubits(self):
        physical_qubits = [pair[1] for pair in self.map]
        return physical_qubits

    # returns isomorphic mapping
    def isomorph(self, shortest_paths):
        GM = isomorphism.GraphMatcher(self.physical_graph, self.logical_graph)
        subgraph_is_iso = GM.subgraph_is_isomorphic()

        if subgraph_is_iso:
            # generate isomorphic mapping
            happy = [(j, i) for i, j in GM.mapping.items()]
        else:
            # to store edges to restore later
            edges_list = {}
            # to store unconnected vertices
            stray_vertices = []
            # to make a priority
            degree_list = sorted(self.logical_graph.degree(weight="weight"), key=lambda node_deg_pair: node_deg_pair[1])

            # reduce ctg until the mapping is found
            while (subgraph_is_iso == False):
                node = degree_list.pop(0)[0]

                # should store all the edges with it
                edges_list[node] = list(self.logical_graph.edges(node, data=True))

                # save the node
                stray_vertices.append(node)

                self.logical_graph.remove_node(node)
                GM = isomorphism.GraphMatcher(self.physical_graph, self.logical_graph)
                subgraph_is_iso = GM.subgraph_is_isomorphic()

            happy = [(j, i) for i, j in GM.mapping.items()]
            taken = [val for letter, val in happy]

            while stray_vertices:
                node_to_append = stray_vertices.pop()
                the_fattest_edge = sorted(edges_list[node_to_append], key=lambda edge: edge[2]["weight"]).pop()
                idx = [letter for letter, val in happy].index(the_fattest_edge[1])
                mapped_node = happy[idx]
                shorter = {k: v for k, v in
                           sorted(shortest_paths[mapped_node[1]].items(), key=lambda item: len(item[1]))}
                for phys_nod in shorter:
                    if phys_nod not in taken:
                        happy.append((node_to_append, phys_nod))
                        taken.append(phys_nod)
                        break

            happy = sorted(happy, key=lambda el: el[0])

        self.map = happy

    def construct_ctg(self, variables, gates):
        self.set_nodes_logical(variables)

        for gate in gates:
            if gate.name == 'h' or gate.name == 'H' or gate.name == 'T' or gate.name == 'T+' or gate.name == 'T*':
                continue
            elif gate.name == 'x' or gate.name == 't1':
                continue
            # do only until t5
            elif gate.name.startswith('t') and len(gate.variables) == 3:
                a = gate.variables[0]
                b = gate.variables[1]
                c = gate.variables[2]
                # cnot on a b c
                self.logical_add_weight(b, c)
                self.logical_add_weight(a, c)
                self.logical_add_weight(b, c)

            elif gate.name.startswith('t') and len(gate.variables) == 4:
                t0 = 'ancilla' + str(self.ancilla_num)
                self.logical_graph.add_node(t0)
                self.ancilla_num += 1
                a = gate.variables[0]
                b = gate.variables[1]
                c = gate.variables[2]
                d = gate.variables[3]
                # cnot on a b t0
                self.logical_add_weight(b, t0)
                self.logical_add_weight(a, t0)
                self.logical_add_weight(b, t0)
                # cnot on t0 c d
                self.logical_add_weight(c, d)
                self.logical_add_weight(t0, d)
                self.logical_add_weight(c, d)
                # cnot on a b t0
                self.logical_add_weight(b, t0)
                self.logical_add_weight(a, t0)
                self.logical_add_weight(b, t0)

            elif gate.name.startswith('t') and len(gate.variables) == 5:
                t0 = 'ancilla' + str(self.ancilla_num)
                self.logical_graph.add_node(t0)
                self.ancilla_num += 1
                t1 = 'ancilla' + str(self.ancilla_num)
                self.logical_graph.add_node(t1)
                self.ancilla_num += 1
                a = gate.variables[0]
                b = gate.variables[1]
                c = gate.variables[2]
                d = gate.variables[3]
                e = gate.variables[4]
                # cnot on a b t0
                self.logical_add_weight(b, t0)
                self.logical_add_weight(a, t0)
                self.logical_add_weight(b, t0)
                # cnot on t0 c t1
                self.logical_add_weight(c, t1)
                self.logical_add_weight(t0, t1)
                self.logical_add_weight(c, t1)
                # cnot on t1 d e
                self.logical_add_weight(d, e)
                self.logical_add_weight(t1, e)
                self.logical_add_weight(d, e)
                # cnot on t0 c t1
                self.logical_add_weight(c, t1)
                self.logical_add_weight(t0, t1)
                self.logical_add_weight(c, t1)
                # cnot on a b t0
                self.logical_add_weight(b, t0)
                self.logical_add_weight(a, t0)
                self.logical_add_weight(b, t0)
            else:
                if gate.name == 'v':
                    self.logical_add_weight(gate.variables[0], gate.variables[1])
                    self.logical_add_weight(gate.variables[0], gate.variables[1])

                elif gate.name == 'v+':
                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                elif gate.name == 'H' or gate.name == 'h':
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                elif gate.name == 'T':
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                elif gate.name == 'T+' or gate.name == 'T*':
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                #                    self.logical_add_weight(gate.variables[1], gate.variables[0])
                elif gate.name == 'cx' or gate.name == 't2' or gate.name == 'sw':
                    self.logical_add_weight(gate.variables[0], gate.variables[1])
                else:
                    print("[INFO] Error inserting gates to ctg. Unknown gate {}".format(gate))

    def count_swap(self, mapping, physical_paths, ctg):
        numswap = 0

        # print(mapping)
        # print(physical_paths)
        # print(ctg)

        for edge in ctg:
            node1 = mapping[edge[0]]
            node2 = mapping[edge[1]]
            if len(physical_paths[node1][node2]) != 0:
                numswap += (len(physical_paths[node1][node2])) * 2

        return numswap



def main():
    # log_g = nx.Graph()
    # phys_g = nx.Graph()

    graphs = Mapping()

    # log_g.add_weighted_edges_from([(0,1,73), (1,2,140), (2,3,52), (3,4,13), (5,4,7)])
    graphs.set_nodes_logical([0, 1, 2, 3, 4, 5])

    print(graphs)

    graphs.logical_add_weight(0, 1, 73)
    graphs.logical_add_weight(1, 2, 140)
    graphs.logical_add_weight(2, 3, 52)
    graphs.logical_add_weight(3, 4, 13)
    graphs.logical_add_weight(5, 4, 7)

    # phys_g.add_edges_from([(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,8), (8,7), (5,9), (4,10),(3,11), (2,12),(1,13), (13,12),(12,11), (11,10),(10,9), (9,8)])

    graphs.set_nodes_physical(
        [[0, 1], [0, 14], [1, 0], [1, 2], [1, 13], [2, 1], [2, 3], [2, 12], [3, 2], [3, 4], [3, 11], [4, 3], [4, 5],
         [4, 10], [5, 4], [5, 6], [5, 9], [6, 5], [6, 8], [7, 8], [8, 6], [8, 7], [8, 9], [9, 5], [9, 8], [9, 10],
         [10, 4], [10, 9], [10, 11], [11, 3], [11, 10], [11, 12], [12, 2], [12, 11], [12, 13], [13, 1], [13, 12],
         [13, 14], [14, 0], [14, 13]])
    graphs.physical_add_edges(
        [[0, 1], [0, 14], [1, 0], [1, 2], [1, 13], [2, 1], [2, 3], [2, 12], [3, 2], [3, 4], [3, 11], [4, 3], [4, 5],
         [4, 10], [5, 4], [5, 6], [5, 9], [6, 5], [6, 8], [7, 8], [8, 6], [8, 7], [8, 9], [9, 5], [9, 8], [9, 10],
         [10, 4], [10, 9], [10, 11], [11, 3], [11, 10], [11, 12], [12, 2], [12, 11], [12, 13], [13, 1], [13, 12],
         [13, 14], [14, 0], [14, 13]])

    print(graphs)

    graphs.test_function()

    print(graphs)


if __name__ == "__main__":
    main()

# returns random mapping of varibles to physical qubits
# def random_mapping(self):
#     n = len(var_list)
#     mapping_array = list(range(1, n + 1))
#     random.shuffle(mapping_array)
#     self.map = [(var_list[i], mapping_array[i]) for i in range(n)]

# returns optimised mapping of varibles to physical qubits
# def optimized_mapping(self):
#     # sort physical degrees, logical degrees
#     phys_degree_sequence = [n for n, d in sorted(self.physical_graph.degree(), key=lambda node_deg_pair : node_deg_pair[1], reverse=True)]
#     logic_degree_sequence = [n for n, d in sorted(self.logical_graph.degree(weight="weight"), key=lambda node_deg_pair : node_deg_pair[1], reverse=True)]

#     self.map = list(zip(logic_degree_sequence, phys_degree_sequence))
