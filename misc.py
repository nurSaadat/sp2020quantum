"""misc.py: Implements isomorphism based quantum mapping algorithm"""

__author__ = "Saadat Nursultan"
__email__ = "saadat.nursultan@nu.edu.kz"

import datetime
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import os
import random
import sys
from typing import List, Dict
from networkx.algorithms import isomorphism
# import networkx.algorithms.isomorphism as iso
import itertools

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
        # create edge notaion
        e = (node1, node2, weight)
        if self.logical_graph.has_edge(*e[:2]):
            # add weight value to the weight
            self.logical_graph[node1][node2]['weight'] += weight
        else:
            # create a new edge
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

    # This function takes an edge-to-edge mapping (e.g. found by using graph matcher 
    # on the line graph representations of two graphs) and converts it into node-to-node mapping
    def lineGraphRemapping(self, lineGraphMapping):
        mappingFound = set()
        mappingTaken = set()
        mapping = list()
        potentialyFound = set()
        
        for edgeMapping in lineGraphMapping:
            edgeG1, edgeG2 = edgeMapping
            for nodeG1 in edgeG1:
                if nodeG1 not in mappingFound:
                    for nodeG2 in edgeG2:
                        if (nodeG1, nodeG2) not in potentialyFound:
                            potentialyFound.add((nodeG1, nodeG2))
                        else:
                            mappingFound.add(nodeG1)
                            mappingTaken.add(nodeG2)
                            mapping.append((nodeG1, nodeG2))
                            break
        for remaning in potentialyFound:
            nodeG1, nodeG2 = remaning
            if (nodeG1 not in mappingFound) and (nodeG2 not in mappingTaken):
                mappingTaken.add(nodeG2)
                mapping.append(remaning)
        
        return mapping

    # this function checks whether G1 contains a subgraph isomorphic to G2 by using Whitney isomorphism theorem
    # returns boolean and isomorphism.GraphMatcher
    def subgraphIsomorphismCheck(self, G1, G2):
        # transform graphs into line graphs and check for subgraph isomorphism
        # isomorphism.GraphMatcher tries to find an induced subgraph of G1, such that it is isomorphic to G2. Consequently, if G2 is non-induced subgraph of G1, the algorithm will return False
        GM = isomorphism.GraphMatcher(nx.line_graph(G1), nx.line_graph(G2))
        subgraph_is_iso = GM.subgraph_is_isomorphic()

        # check for exceptions
        # e.g. line graphs of K_3 triangle graph and K_1,3 claw graph are isomorphic, but the original graphs are not
        if subgraph_is_iso:
            edgeListG1 = []
            edgeListG2 = []

            for edgeMaping in GM.mapping.items():
                edgeListG1.append(edgeMaping[0])
                edgeListG2.append(edgeMaping[1])
            
            # let's construct the graphs the algorithm thinks are isomorphic and check them for a quick isomorphism.is_isomorphic
            testG1 = nx.Graph(edgeListG1)
            testG2 = nx.Graph(edgeListG2)
            subgraph_is_iso = isomorphism.is_isomorphic(testG1, testG2)

        return subgraph_is_iso, GM

    # returns isomorphic mapping
    def isomorphOptimistic(self, shortest_paths):

        elarge = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] > 5]
        esmall = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] <= 5]

        pos = nx.spring_layout(self.logical_graph)  # positions for all nodes

        # nodes
        nx.draw_networkx_nodes(self.logical_graph, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.logical_graph, pos, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.logical_graph, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # labels
        nx.draw_networkx_labels(self.logical_graph, pos, font_size=20, font_family="sans-serif")

        plt.axis("off")
        plt.show()

        # check if already ismorphic
        subgraph_is_iso, GM = self.subgraphIsomorphismCheck(self.physical_graph, self.logical_graph)

        if subgraph_is_iso:
            # generate isomorphic mapping
            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.lineGraphRemapping(happy)
        else:     
            # list of disconnecting edges
            disconnecting_edges = []

            # reduce ctg until the mapping is found
            while not subgraph_is_iso:
                # sort edges in non-increasing order (queue)
                edges_list = sorted(self.logical_graph.edges.data('weight'), key=lambda node_node_weight: node_node_weight[2])
                
                # remove disconnecting edges
                for e in disconnecting_edges:
                    edges_list.remove(e)

                # look if there other edges with the same weight
                weights_list = [ (u, v, wt) for (u, v, wt) in edges_list if wt == edges_list[0][2] ]
                
                if len(weights_list) > 1:
                    # select the edge wich will reduce the overall graph degree
                    to_be_popped_edge = weights_list.pop(0)
                    maximal_degree = max(self.logical_graph.degree(to_be_popped_edge[0], weight='weight'), self.logical_graph.degree(to_be_popped_edge[1], weight='weight'))
                    for e in weights_list:
                        curr_deg = max(self.logical_graph.degree(e[0], weight='weight'), self.logical_graph.degree(e[1], weight='weight'))
                        if curr_deg > maximal_degree:
                            maximal_degree = curr_deg
                            to_be_popped_edge = e

                    edge_weight = to_be_popped_edge   

                else:
                    # take the edge with the least weight
                    edge_weight = edges_list.pop(0)
                
                # print( self.logical_graph.edges.data('weight') )
                # print( "removed ", edge_weight[0], edge_weight[1] )

                # remove the edge with the least weight
                self.logical_graph.remove_edge(edge_weight[0], edge_weight[1])

                # if the graph is disconnected, return the edge back
                if not nx.is_connected(self.logical_graph):
                    self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                    disconnecting_edges.append(edge_weight)
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * 2)       

                # check for isomorphism   
                subgraph_is_iso, GM = self.subgraphIsomorphismCheck(self.physical_graph, self.logical_graph)


            # print( self.logical_graph )
            
            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.lineGraphRemapping(happy)
            
        happy = sorted(happy, key=lambda el: el[0])
        print("HAPPPPPPYYYYYYYYYYY", happy)
        self.map = happy
    
    def buildReducedGraph(self, log_to_phys_map):
        # divide edges into two categories
        elarge = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] > 10]
        esmall = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] <= 10]
        # positions for all nodes
        pos = nx.spring_layout(self.logical_graph)  
        # nodes
        nx.draw_networkx_nodes(self.logical_graph, pos, node_size=700)
        # edges
        nx.draw_networkx_edges(self.logical_graph, pos, width=6)
        # labels
        nx.draw_networkx_labels(self.logical_graph, pos, font_size=20, font_family="sans-serif")
        plt.axis("off")
        

    # tries to remove edges such that one, or more potential physical placements appeares
    def figureOutWrongEdge(self, logical_node, permutations, use_permutations, physical_node_list, mapping, removed_edges):
        
        if not use_permutations:
            # get all edges for the logical_node
            edges = [ (u, v, wt) for (u, v, wt) in self.logical_graph.edges.data('weight') if (u == logical_node[0]) or (v == logical_node[0]) ]
            edges = sorted(edges, key=lambda node_node_weight: node_node_weight[2])
            # get all permutations to go through all possible combinations
            # ussually a node will have up to 4 edges, so number of permutations should be low
            permutations = list(itertools.permutations(edges))

        try:
            # prepare lists
            potential_physical_nodes = []
            edges_list = list(permutations.pop())

            # run the while loop until there are any potential placement, or we pop from an empty list
            while len(potential_physical_nodes) == 0:

                # take the edge with the least weight
                # if no more edges, then this will trigger the except
                edge_weight = edges_list.pop(0)

                # remove the edge with the least weight
                self.logical_graph.remove_edge(edge_weight[0], edge_weight[1])

                # if the graph is disconnected, return the edge back
                if not nx.is_connected(self.logical_graph):
                    self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * 2)
                    # record removed edges for a potential rollback
                    removed_edges.append([edge_weight, alternative_path])

                    # recalculate the potential placements
                    # prepare potential_physical_nodes for intersection operation
                    potential_physical_nodes = physical_node_list.copy()
                    parents = []
                    # to what placed logical nodes the current node is connected?
                    for lNode, pNode in mapping:
                        if self.logical_graph.has_edge(logical_node[0], lNode):
                            parents.append(pNode)
                    # make potential physical node list according to the neiboring nodes to the just mapped physical node
                    for parentNode in parents:
                        potential = []
                        for node, degree in physical_node_list:
                            if self.physical_graph.has_edge(parentNode, node):
                                potential.append((node, degree))
                        potential_physical_nodes = sorted(list(set(potential_physical_nodes).intersection(potential)), key = lambda node_deg_pair: node_deg_pair[1])
            
            return potential_physical_nodes
        except IndexError:
            # return all removed edges
            for edge_weight, alternative_path in removed_edges:
                self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                # subtract 2 * (weight of removed edge) to every edge on the alternative path
                for i in range(len(alternative_path) - 1):
                    self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))
            removed_edges.clear()

            if len(permutations) > 0:
                return self.figureOutWrongEdge(logical_node, permutations, True, physical_node_list, mapping, removed_edges)
            else:
                return []

    # BFS-like algorithm to find placement of logical nodes onto physical nodes
    # for the first run, the node_queue should contain the root node (usually a node with biggest degree)
    def placeNodeOnNode(self, node_queue, potential_physical_nodes, use_potential, logical_node_list, physical_node_list, mapping):

        # save the state
        saved_node_queue = node_queue.copy()
        saved_logical_node_list = logical_node_list.copy()
        saved_physical_node_list = physical_node_list.copy()
        saved_mapping = mapping.copy()

        # if node_queue is empty, then we are done
        if len(node_queue) == 0:
            return True
        # get the logical node
        logical_node = node_queue.pop(0)

        if not use_potential:

            # if mapping is empty, then algorithm only just started
            if len(mapping) == 0:
                potential_physical_nodes = physical_node_list.copy()
            # else find intersection of all neighboring nodes of already placed logical parents
            else:
                # prepare potential_physical_nodes for intersection operation
                potential_physical_nodes = physical_node_list.copy()
                parents = []
                # to what placed logical nodes the current node is connected?
                for lNode, pNode in mapping:
                    if self.logical_graph.has_edge(logical_node[0], lNode):
                        parents.append(pNode)
                # make potential physical node list according to the neiboring nodes to the just mapped physical node
                for parentNode in parents:
                    potential = []
                    for node, degree in physical_node_list:
                        if self.physical_graph.has_edge(parentNode, node):
                            potential.append((node, degree))
                    potential_physical_nodes = sorted(list(set(potential_physical_nodes).intersection(potential)), key = lambda node_deg_pair: node_deg_pair[1])
        # initiate a try/excpet block to cycle through all potential physical nodes in case of wrong placement
        try:
            # list of disconnecting edges
            disconnecting_edges = []
            # list of removed edges
            removed_edges = [] 

            # try to find more placements
            if len(potential_physical_nodes) == 0:
                potential_physical_nodes = self.figureOutWrongEdge(logical_node, [], False, physical_node_list, mapping, removed_edges)

            # if there is no potential placements by this point, preveious node was placed wrong
            if len(potential_physical_nodes) == 0:
                return False

            physical_node = potential_physical_nodes.pop()
            physical_node_list.remove(physical_node)

            # before comparing degrees, we need to update the degree of the logical_node because it could have been changed
            logical_node = (logical_node[0], self.logical_graph.degree()[logical_node[0]])

            # reduce edges until equal
            # if the degree of the logical node is the same, or less than the degree of physical node, then no problems
            while logical_node[1] > physical_node[1]:
                edges_list = [ (u, v, wt) for (u, v, wt) in self.logical_graph.edges.data('weight') if (u == logical_node[0]) or (v == logical_node[0]) ]
                edges_list = sorted(edges_list, key=lambda node_node_weight: node_node_weight[2])

                # remove disconnecting edges
                for e in disconnecting_edges:
                    edges_list.remove(e)
            
                # take the edge with the least weight
                # if no more edges, then this will trigger the except
                edge_weight = edges_list.pop(0)

                # remove the edge with the least weight
                self.logical_graph.remove_edge(edge_weight[0], edge_weight[1])

                # if the graph is disconnected, return the edge back
                if not nx.is_connected(self.logical_graph):
                    self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                    disconnecting_edges.append(edge_weight)
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * 2)
                    # record removed edges for a potential rollback
                    removed_edges.append([edge_weight, alternative_path])
                    # update the node degree
                    logical_node = (logical_node[0], self.logical_graph.degree()[logical_node[0]])
                
            # now nodes have the same degree
            mapping.append((logical_node[0], physical_node[0]))

            # now we need to go through all the neighbours
            # in order to prevent errors with the for loop we will make a temporary copy of logical_node_list
            temp_logical_node_list = logical_node_list.copy()
            for node, degree in logical_node_list:
                if self.logical_graph.has_edge(logical_node[0], node):
                    temp_logical_node_list.remove((node, degree))
                    node_queue.append((node, degree))

            logical_node_list = temp_logical_node_list

            # next, go through all nodes in the node_queue
            if self.placeNodeOnNode(node_queue, [], False, logical_node_list, physical_node_list, mapping):
                return True
            else:
                raise IndexError

        except IndexError:
            # return all removed edges
            for edge_weight, alternative_path in removed_edges:
                self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                # subtract 2 * (weight of removed edge) to every edge on the alternative path
                for i in range(len(alternative_path) - 1):
                    self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))

            # if there are no more potential physical edges, then placement of the previous node is wrong
            if len(potential_physical_nodes) > 0:
                # if placeNodeOnNode returned True, then we need to record changes in the saved_mapping into mapping
                if self.placeNodeOnNode(saved_node_queue, potential_physical_nodes, True, saved_logical_node_list, saved_physical_node_list, saved_mapping):
                    mapping.clear()
                    for item in saved_mapping:
                        mapping.append(item)
                    return True
                else:
                    return False
            else:
                return False

    # returns isomorphic mapping
    def isomorph(self, shortest_paths, file_name):

        elarge = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] > 5]
        esmall = [(u, v) for (u, v, d) in self.logical_graph.edges(data=True) if d["weight"] <= 5]

        pos = nx.spring_layout(self.logical_graph)  # positions for all nodes

        # nodes
        nx.draw_networkx_nodes(self.logical_graph, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.logical_graph, pos, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.logical_graph, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # labels
        nx.draw_networkx_labels(self.logical_graph, pos, font_size=20, font_family="sans-serif")

        plt.axis("off")
        # plt.show()

        # retrieve date
        today = datetime.datetime.today()
        # split file path
        directories = file_name.split("/")
        # make figures directory
        os.makedirs('./figures/', exist_ok=True)
        # create file name
        file_name = './figures/' + directories[-1][:-5] + today.strftime("%Y%m%d%H%M%S") + ".jpeg"
        # save graph
        plt.savefig(file_name)

        # check if already ismorphic
        subgraph_is_iso, GM = self.subgraphIsomorphismCheck(self.physical_graph, self.logical_graph)

        if subgraph_is_iso:
            # generate isomorphic mapping 
            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.lineGraphRemapping(happy)
        else:
            # sort all nodes by their degree 
            logical_degree_list = sorted(self.logical_graph.degree(), key=lambda node_deg_pair: node_deg_pair[1])
            physical_degree_list = sorted(self.physical_graph.degree(), key=lambda node_deg_pair: node_deg_pair[1])
            # copy the physical degree list as a list of potential physical node placements
            potential_physical_nodes = physical_degree_list.copy()
            # list for mapping
            mapping = []
            # pop nodes with the biggest degree
            logical_node = logical_degree_list.pop()

            # let's work like in BFS
            # queue of nodes to be done
            node_queue = [logical_node]
            # start the algorithm
            result = self.placeNodeOnNode(node_queue, [], False, logical_degree_list, physical_degree_list, mapping)

            if result:
                happy = mapping
            else:
                raise NotImplementedError("Mapping not found")

            
        happy = sorted(happy, key=lambda el: el[0])
        # print("HAPPPPPPYYYYYYYYYYY", happy)
        self.map = happy
        self.buildReducedGraph(happy)

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

    graphs.isomorph()

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
