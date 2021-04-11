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
import itertools


class Mapping:
    """
    This is a class for a mapping from logical circuit to physical architecture.

    Attributes: 
    map (List[("logical_node_string", physical_node_int)]): Mapping of logical circuit to a physcial architecture.
    physical graph (NetworkX Graph): Physical circuit configuration.
    logical graph (NetworkX Graph): Circuit Interaction Graph (refer to the paper).
    """

    def __init__(self):
        self.logical_graph = nx.Graph()
        self.ancilla_num = 0
        self.physical_graph = nx.Graph()
        self.map = []

        self.animCount = 0

    def __repr__(self):
        # list(self.logical_graph.nodes(data=True)
        return "Logical mapping:\n {} \nPhysical mapping:\n {} \nLogical to physical mapping:\n {} \n".format(
            list(self.logical_graph.edges(data=True)), list(self.physical_graph.edges()), list(self.map))

    def set_nodes_physical(self, coupling_list: List[List[int]]):
        """
        Adds nodes to the physical graph.

        Parameters:
        coupling_list (List[List[int]]): Graph description of the physical architecture.

        Returns: 
        None

        Example:
        set_nodes_physical([1, 2, 3])
        """
        flat_list = [item for sublist in coupling_list for item in sublist]
        self.physical_graph.add_nodes_from(list(dict.fromkeys(flat_list)))

    def set_nodes_logical(self, variables: List[str]):
        """
        Adds nodes to the logical graph.

        Parameters:
        variables (List[str]): Graph description of the logical circuit.

        Returns: 
        None

        Example:
        set_nodes_logical([1, 2, 3])
        """
        self.logical_graph.add_nodes_from(variables)

    def physical_add_edges(self, coupling_list: List[List[int]]):
        """
        Adds undirected unweighted edges to the physical graph.

        Parameters:
        coupling_list (List[List[int]]): Graph description of the physical architecture.

        Returns: 
        None
        """
        for item in coupling_list:
            if not self.physical_graph.has_edge(item[0], item[1]) or not self.physical_graph.has_edge(item[1], item[0]):
                self.physical_graph.add_edge(item[0], item[1])
            else:
                continue

    def logical_add_weight(self, node1: str, node2: str, weight=1):
        """
        Adds undirected weighted edge to the logical graph if it doesn't exist.

        Parameters:
        node1 (str): Name of first node.
        node2 (str): Name of second node.
        weight (int): The weight that is going to be added to the edge between node1 and node2.

        Returns:
        None
        """
        # create edge notaion
        e = (node1, node2, weight)
        if self.logical_graph.has_edge(*e[:2]):
            # add weight value to the weight
            self.logical_graph[node1][node2]['weight'] += weight
        else:
            # create a new edge
            self.logical_graph.add_weighted_edges_from([e])

    def physical_degree_is_less(self):
        """
        Determines whether degree of physical architecture less than one of logical graph.

        Parameters:
        None

        Returns:
        bool: Is degree of physical architecture less than one of logical graph.
        """
        degree_sequence = sorted(
            [d for n, d in self.logical_graph.degree(weight="weight")], reverse=True)
        max_logical_degree = max(degree_sequence)
        degree_sequence = sorted(
            [d for n, d in self.physical_graph.degree()], reverse=True)
        max_physical_degree = max(degree_sequence)

        if (max_physical_degree < max_logical_degree):
            return True
        else:
            return False

    def get_mapping(self):
        """
        Gets logical-to-physical mapping for logical circuit qubits and ancilla qubits.

        Parameters:
        None

        Returns:
        variable_mapping (List[(str, int)]): The mapping from logical to physical qubits.
        ancilla_mapping (List[(str, int)]): The mapping from logical to physical ancilla qubits.
        """
        variable_mapping = []
        ancilla_mapping = []
        for (k, v) in self.map:
            if k.startswith('ancilla'):
                ancilla_mapping.append((k, v))
            else:
                variable_mapping.append((k, v))
        return variable_mapping, ancilla_mapping

    def get_physical_qubits(self):
        """
        Gets physical qubits.

        Parameters:
        None

        Returns:
        List[int]: The list of physical qubits used.
        """
        physical_qubits = [pair[1] for pair in self.map]
        return physical_qubits

    def line_graph_remapping(self, line_graph_mapping):
        """
        Takes an edge-to-edge mapping 
        (e.g. found by using graph matcher on the line graph representations of two graphs) 
        and converts it into node-to-node mapping.

        Parameters: 
        lineGraphMapping (List[(logical edge, physical edge)]): Edge-to-edge mapping.

        Returns:
        mapping (List[(logical edge, physical edge)]): Node-to-node mapping.
        """
        mappingFound = set()
        mappingTaken = set()
        mapping = list()
        potentialyFound = set()

        for edgeMapping in line_graph_mapping:
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

    def subgraphIsomorphismCheck(self, G1, G2):
        """
        Checks whether G1 contains a subgraph isomorphic to G2 by using Whitney isomorphism theorem.

        Parameters:
        G1 (NetworkX graph): The bigger graph.
        G2 (NetworkX graph): The smaller graph.

        Returns:
        bool: Is graph G2 isomorphic to a subgraph in G1.
        isomorphism.GraphMatcher: Graph matcher object with parameters.
        """
        # transform graphs into line graphs and check for subgraph isomorphism
        # isomorphism.GraphMatcher tries to find an induced subgraph of G1, such that it is isomorphic to G2.
        # Consequently, if G2 is non-induced subgraph of G1, the algorithm will return False
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

    def isomorphOptimistic(self):
        """
        Checks whether the logical graph and physical graphs are isomorphic and creates a mapping.

        Parameters:
        None

        Returns:
        None
        """
        elarge = [(u, v) for (u, v, d) in self.logical_graph.edges(
            data=True) if d["weight"] > 5]
        esmall = [(u, v) for (u, v, d) in self.logical_graph.edges(
            data=True) if d["weight"] <= 5]

        pos = nx.spring_layout(self.logical_graph)  # positions for all nodes

        # nodes
        nx.draw_networkx_nodes(self.logical_graph, pos, node_size=700)

        # edges
        nx.draw_networkx_edges(self.logical_graph, pos,
                               edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.logical_graph, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )

        # labels
        nx.draw_networkx_labels(self.logical_graph, pos,
                                font_size=20, font_family="sans-serif")

        plt.axis("off")
        plt.show()

        # check if already ismorphic
        subgraph_is_iso, GM = self.subgraphIsomorphismCheck(
            self.physical_graph, self.logical_graph)

        if subgraph_is_iso:
            # generate isomorphic mapping
            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.line_graph_remapping(happy)
        else:
            # list of disconnecting edges
            disconnecting_edges = []

            # reduce ctg until the mapping is found
            while not subgraph_is_iso:
                # sort edges in non-increasing order (queue)
                edges_list = sorted(self.logical_graph.edges.data(
                    'weight'), key=lambda node_node_weight: node_node_weight[2])

                # remove disconnecting edges
                for e in disconnecting_edges:
                    edges_list.remove(e)

                # look if there other edges with the same weight
                weights_list = [(u, v, wt) for (u, v, wt)
                                in edges_list if wt == edges_list[0][2]]

                if len(weights_list) > 1:
                    # select the edge wich will reduce the overall graph degree
                    to_be_popped_edge = weights_list.pop(0)
                    maximal_degree = max(self.logical_graph.degree(
                        to_be_popped_edge[0], weight='weight'), self.logical_graph.degree(to_be_popped_edge[1], weight='weight'))
                    for e in weights_list:
                        curr_deg = max(self.logical_graph.degree(
                            e[0], weight='weight'), self.logical_graph.degree(e[1], weight='weight'))
                        if curr_deg > maximal_degree:
                            maximal_degree = curr_deg
                            to_be_popped_edge = e

                    edge_weight = to_be_popped_edge

                else:
                    # take the edge with the least weight
                    edge_weight = edges_list.pop(0)

                # remove the edge with the least weight
                self.logical_graph.remove_edge(edge_weight[0], edge_weight[1])

                # if the graph is disconnected, return the edge back
                if not nx.is_connected(self.logical_graph):
                    self.logical_add_weight(
                        edge_weight[0], edge_weight[1], edge_weight[2])
                    disconnecting_edges.append(edge_weight)
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(
                        self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(
                            alternative_path[i], alternative_path[i+1], edge_weight[2] * 2)

                # check for isomorphism
                subgraph_is_iso, GM = self.subgraphIsomorphismCheck(
                    self.physical_graph, self.logical_graph)

            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.line_graph_remapping(happy)

        happy = sorted(happy, key=lambda el: el[0])
        # print("Happy mapping: ", happy)
        self.map = happy

    def drawGraph(self, file_name, is_logical=True):
        """
        Visualizes the graph representation.

        Parameters:
        file_name (str): The name of the file where the circuit is stored.
        is_logical (bool): Does the graph represent the logical circuit (the opposite is physical architecture graph). 

        Returns:
        graph_image (str): The name of the file, where the image is stored.
        """
        plt.figure(figsize=(6, 4))
        elarge = [(u, v) for (u, v, d) in self.logical_graph.edges(
            data=True) if d["weight"] > 5]
        esmall = [(u, v) for (u, v, d) in self.logical_graph.edges(
            data=True) if d["weight"] <= 5]
        # positions for all nodes
        pos = nx.spring_layout(self.logical_graph)
        # nodes
        nx.draw_networkx_nodes(self.logical_graph, pos, node_size=700)
        # edges
        nx.draw_networkx_edges(self.logical_graph, pos,
                               edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            self.logical_graph, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )
        # labels
        nx.draw_networkx_labels(self.logical_graph, pos,
                                font_size=20, font_family="sans-serif")
        plt.axis("off")
        # retrieve date
        today = datetime.datetime.today()
        # make outputs/ directory
        os.makedirs('./outputs/', exist_ok=True)
        if (is_logical):
            os.makedirs('./outputs/input/', exist_ok=True)
            # create file name
            graph_image = './outputs/input/{}_{}.jpeg'.format(
                file_name, today.strftime("%Y%m%d%H%M%S"))
        else:
            os.makedirs('./outputs/reduced/', exist_ok=True)
            # create file name
            graph_image = './outputs/reduced/{}_{}.jpeg'.format(
                file_name, today.strftime("%Y%m%d%H%M%S"))

        # save graph
        plt.savefig(graph_image)
        if (is_logical):
            plt.clf()
        # return the name
        return graph_image

    def figureOutWrongEdge(self, logical_node, permutation_list, physical_node_list, mapping, removed_edges):
        """
        Recursively tries to remove edges such that one, or more potential physical placements appeares.

        Parameters:
        logical_node (tuple(str, int)): The logical node from the node queue.
        permutation_list (List[n-tuple((node1, node2, weight))]): order of edges to be removed
        physical_node_list (List[(int, int)]): Physical degrees by degrees.
        mapping (List[(str, int)]): Resulting mapping from logical circuit to physical architecture.
        removed_edges (List[[(node1, node2, weight), List[int]]]): Record of removed edges for a potential rollback.

        Returns:
        a list of physical nodes or an empty list if none were found.
        """
        try:
            # prepare list
            potential_physical_nodes = []

            # run the while loop until there are any potential placement, or we pop from an empty list
            while len(potential_physical_nodes) == 0:

                # take the edge with the least weight
                # if no more edges, then this will trigger the except
                edge_weight = permutation_list.pop(0)

                # the weight of the poped edge may have changed
                real_weight = self.logical_graph[edge_weight[0]][edge_weight[1]]['weight']

                # remove the edge with the least weight
                self.logical_graph.remove_edge(edge_weight[0], edge_weight[1])

                # if the graph is disconnected, return the edge back
                if not nx.is_connected(self.logical_graph):
                    self.logical_add_weight(
                        edge_weight[0], edge_weight[1], real_weight)
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(
                        self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(
                            alternative_path[i], alternative_path[i+1], real_weight * 2)
                    # record removed edges for a potential rollback
                    removed_edges.append(
                        [(edge_weight[0], edge_weight[1], real_weight), alternative_path])

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
                        potential_physical_nodes = sorted(list(set(potential_physical_nodes).intersection(
                            potential)), key=lambda node_deg_pair: node_deg_pair[1])

            return potential_physical_nodes
        except IndexError:
            # return all removed edges
            for edge_weight, alternative_path in removed_edges:
                self.logical_add_weight(
                    edge_weight[0], edge_weight[1], edge_weight[2])
                # subtract 2 * (weight of removed edge) to every edge on the alternative path
                for i in range(len(alternative_path) - 1):
                    self.logical_add_weight(
                        alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))
            removed_edges.clear()

            return []

    def anim(self):
        animation = "|/-\\"

        os.write(1, str.encode('\r' + animation[self.animCount % len(animation)]))
        
        if self.animCount > 99:
            self.animCount = 0
        else:
            self.animCount += 1

    def placeNodeOnNode(self, node_queue, potential_physical_nodes, use_potential, figureOuted_before, logical_node_list, physical_node_list, mapping):
        """
        BFS-like algorithm to find placement of logical nodes onto physical nodes.
        For the first run, the node_queue should contain the root node (usually a node with biggest degree)

        Parameters:
        node_queue (List[(node, degree)]): queue of logical graph nodes.
        potential_physical_nodes (List[int]): copy of the physical degree list as a list of potential physical node placements.
        use_potential (bool): whether the list of potential physical node placement should be used. False when the potential_physical_nodes is empty.
        logical_node_list (List[(str, int)]): logical nodes sorted by degrees.
        physical_node_list (List[(int, int)]): physical nodes sorted by degrees.
        mapping (List[(str, int)]): resulting mapping from logical circuit to physical architecture.

        Returns:
        bool: can the logical circuit be mapped to the physical architecture.

        Raises:
        IndexError
        """

        # if node_queue is empty, then we are done
        if len(node_queue) == 0:
            # return True
            return (True, True)
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
                    potential_physical_nodes = sorted(list(set(potential_physical_nodes).intersection(
                        potential)), key=lambda node_deg_pair: node_deg_pair[1])
        # initiate a try/excpet block to cycle through all potential physical nodes in case of wrong placement
        # self.anim()
        try:
            # list of disconnecting edges
            disconnecting_edges = []
            # list of removed edges
            removed_edges = []

            # boolean to return at the end
            figureOuted = figureOuted_before

            # try to find more placements
            if (len(potential_physical_nodes) == 0) and (not figureOuted):
                # get all edges for the logical_node
                edges = [(u, v, wt) for (u, v, wt) in self.logical_graph.edges.data(
                    'weight') if (u == logical_node[0]) or (v == logical_node[0])]
                edges = sorted(
                    edges, key=lambda node_node_weight: node_node_weight[2])
                # remove edges that are not connected to already placed nodes
                for (u, v, wt) in edges:
                    placed = False
                    for (logNode, phyNode) in mapping:
                        if (u == logNode) or (v == logNode):
                            placed = True
                            break
                    if not placed:
                        edges.remove((u, v, wt))
                # get all permutations to go through all possible combinations
                # ussually a node will have up to 4 edges, so number of permutations should be low
                permutations = list(itertools.permutations(edges))
                # run a while loop until pernutations is empty
                while len(permutations) > 0:
                    permutation_list = list(permutations.pop())
                    potential_physical_nodes = self.figureOutWrongEdge(logical_node, permutation_list, physical_node_list, mapping, removed_edges)
                    
                    # if there is anything in the potential_physical_nodes, then we finished successfully
                    if len(potential_physical_nodes) > 0:
                        break
            figureOuted = True

                
            # if there is no potential placements by this point, preveious node was placed wrong
            if len(potential_physical_nodes) == 0:
                # return False
                return (False, False, [], [])

            physical_node = potential_physical_nodes.pop()
            physical_node_list.remove(physical_node)

            # before comparing degrees, we need to update the degree of the logical_node because it could have been changed
            logical_node = (logical_node[0], self.logical_graph.degree()[
                            logical_node[0]])

            # reduce edges until equal
            # if the degree of the logical node is the same, or less than the degree of physical node, then no problems
            while logical_node[1] > physical_node[1]:
                edges_list = [(u, v, wt) for (u, v, wt) in self.logical_graph.edges.data(
                    'weight') if (u == logical_node[0]) or (v == logical_node[0])]
                edges_list = sorted(
                    edges_list, key=lambda node_node_weight: node_node_weight[2])

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
                    self.logical_add_weight(
                        edge_weight[0], edge_weight[1], edge_weight[2])
                    disconnecting_edges.append(edge_weight)
                # else adjust weights on the alternative path
                else:
                    alternative_path = nx.shortest_path(
                        self.logical_graph, source=edge_weight[0], target=edge_weight[1], weight='weight')
                    # add 2 * (weight of removed edge) to every edge on the alternative path
                    for i in range(len(alternative_path) - 1):
                        self.logical_add_weight(
                            alternative_path[i], alternative_path[i+1], edge_weight[2] * 2)
                    # record removed edges for a potential rollback
                    removed_edges.append([edge_weight, alternative_path])
                    # update the node degree
                    logical_node = (logical_node[0], self.logical_graph.degree()[
                                    logical_node[0]])

            # now nodes have the same degree
            mapping.append((logical_node[0], physical_node[0]))

            # now we need to go through all the neighbours
            # in order to prevent errors with the for loop we will make a temporary copy of logical_node_list
            temp_logical_node_list = logical_node_list.copy()
            for node, degree in logical_node_list:
                if self.logical_graph.has_edge(logical_node[0], node):
                    temp_logical_node_list.remove((node, degree))
                    # for qNode, qDegree in node_queue:
                    #     if node == qNode:
                    #         node_queue.remove((qNode, qDegree))
                    node_queue.append((node, degree))

            temp = logical_node_list.copy()
            for item in temp:
                if not item in temp_logical_node_list:
                    logical_node_list.remove(item)

            # next, go through all nodes in the node_queue
            return (True, False, removed_edges, potential_physical_nodes, figureOuted)

        except IndexError:
            # return all removed edges
            for edge_weight, alternative_path in removed_edges:
                self.logical_add_weight(
                    edge_weight[0], edge_weight[1], edge_weight[2])
                # subtract 2 * (weight of removed edge) to every edge on the alternative path
                for i in range(len(alternative_path) - 1):
                    self.logical_add_weight(
                        alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))

            return [False, False, [], potential_physical_nodes, figureOuted]

    def isomorph(self, file_name):
        """
        Creates isomorphic mapping.

        Parameters:
        file_name (str): The name of the file where the circuit is stored.

        Returns:
        logical_graph_name (str): Name of the file where the image of the logical graph is stored.
        reduced_graph_name (str): Name of the file where the image og reduced logical graph is stored.
        """
        # save graph image and get its name
        logical_graph_name = self.drawGraph(file_name, is_logical=True)

        # check if already ismorphic
        subgraph_is_iso, GM = self.subgraphIsomorphismCheck(
            self.physical_graph, self.logical_graph)

        if subgraph_is_iso:
            # generate isomorphic mapping
            happy = [(j, i) for i, j in GM.mapping.items()]
            happy = self.line_graph_remapping(happy)
        else:
            # sort all nodes by their degree
            logical_degree_list = sorted(
                self.logical_graph.degree(), key=lambda node_deg_pair: node_deg_pair[1])
            physical_degree_list = sorted(
                self.physical_graph.degree(), key=lambda node_deg_pair: node_deg_pair[1])
            
            # list for mapping
            mapping = []
            # pop nodes with the biggest degree
            logical_node = logical_degree_list.pop()

            # let's work like in BFS
            # queue of nodes to be done
            node_queue = [logical_node]
            # memory for node placement
            saved_node_queue = {}
            saved_logical_node_list = {}
            saved_physical_node_list = {}
            saved_mapping = {}
            saved_removed_edges = {}
            potential_list = {}
            current_node = 0
            use_potential = False
            # memory to not get stuck in figure out wrong edge
            figureOuted = {}
            # save the first node information
            # save node information to return to it if node placement fails
            saved_node_queue[current_node] = node_queue.copy()
            saved_logical_node_list[current_node] = logical_degree_list.copy()
            saved_physical_node_list[current_node] = physical_degree_list.copy()
            saved_mapping[current_node] = mapping.copy()
            figureOuted[current_node] = False
            # start the algorithm
            while True:
                # if we go below 0, then it means this algorithm failed
                if current_node < 0:
                    raise NotImplementedError("Mapping not found")

                # are we placing the next node, or trying to place another node on the same place?
                if use_potential:
                    # another node on the same palce
                    result = self.placeNodeOnNode(node_queue, potential_list[current_node], True, figureOuted[current_node], logical_degree_list, physical_degree_list, mapping)
                else:
                    # the next node
                    result = self.placeNodeOnNode(node_queue, [], False, False, logical_degree_list, physical_degree_list, mapping)
                 
                # was the current node placement successful?
                if not result[0]:
                    # No
                    removed_edges = result[2]
                    # return all removed edges
                    for edge_weight, alternative_path in removed_edges:
                        self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                        # subtract 2 * (weight of removed edge) to every edge on the alternative path
                        for i in range(len(alternative_path) - 1):
                            self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))

                    # check potential_physical_nodes
                    if len(result[3]) == 0:
                        # algorithm failed to place any node after placing the parent node 
                        # so, the parent node was wrong
                        # clear figureOuted memory
                        figureOuted[current_node] = False
                        # go back to the parent node
                        current_node -= 1
                        use_potential = True
                        # return removed_edges by parent
                        removed_edges = saved_removed_edges[current_node].copy()
                        # return all removed edges
                        for edge_weight, alternative_path in removed_edges:
                            self.logical_add_weight(edge_weight[0], edge_weight[1], edge_weight[2])
                            # subtract 2 * (weight of removed edge) to every edge on the alternative path
                            for i in range(len(alternative_path) - 1):
                                self.logical_add_weight(alternative_path[i], alternative_path[i+1], edge_weight[2] * (-2))
                        # return the previous node info
                        node_queue = saved_node_queue[current_node].copy()
                        logical_degree_list = saved_logical_node_list[current_node].copy()
                        physical_degree_list = saved_physical_node_list[current_node].copy()
                        mapping = saved_mapping[current_node].copy()
                    else:
                        # there are more nodes to try
                        use_potential = True
                        # did the algorithm use figureOutWrongEnge()?
                        figureOuted[current_node] = result[4]
                        # don't forget, that placeNodeOnNode pops potential_node_list
                        # return the current node info
                        node_queue = saved_node_queue[current_node].copy()
                        logical_degree_list = saved_logical_node_list[current_node].copy()
                        physical_degree_list = saved_physical_node_list[current_node].copy()
                        mapping = saved_mapping[current_node].copy()
                        # update the potential_list
                        potential_list[current_node] = result[3].copy()
                # did we place all of the nodes?
                elif not result[1]:
                    # No
                    # save the removed edges
                    saved_removed_edges[current_node] = result[2].copy()
                    # save the potential physical nodes for the current (placed) node
                    potential_list[current_node] = result[3]
                    # did the algorithm use figureOutWrongEnge()?
                    figureOuted[current_node] = result[4]
                    # increment the current_node
                    current_node += 1
                    use_potential = False
                    # save node information to return to it if node placement fails
                    saved_node_queue[current_node] = node_queue.copy()
                    saved_logical_node_list[current_node] = logical_degree_list.copy()
                    saved_physical_node_list[current_node] = physical_degree_list.copy()
                    saved_mapping[current_node] = mapping.copy()
                else:
                    happy = mapping
                    break

        happy = sorted(happy, key=lambda el: el[0])
        # print("Happy mapping: ", happy)
        self.map = happy

        # save reduced graph image and get its name
        reduced_graph_name = self.drawGraph(file_name, is_logical=False)
        return logical_graph_name, reduced_graph_name

    def construct_ctg(self, variables, gates):
        """
        Constructs Circuit Interaction Graph (refer to the paper).

        Parameters:
        variables (List[str]): Nodes of circuit graph. 
        gates (List[Gate]): Gates used in the circuit.  

        Returns:
        None
        """
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
                    self.logical_add_weight(
                        gate.variables[0], gate.variables[1])
                    self.logical_add_weight(
                        gate.variables[0], gate.variables[1])

                elif gate.name == 'v+':
                    self.logical_add_weight(
                        gate.variables[1], gate.variables[0])
                    self.logical_add_weight(
                        gate.variables[1], gate.variables[0])
                elif gate.name == 'cx' or gate.name == 't2' or gate.name == 'sw':
                    self.logical_add_weight(
                        gate.variables[0], gate.variables[1])
                else:
                    print(
                        "[INFO] Error inserting gates to ctg. Unknown gate {}".format(gate))

    def count_swap(self, mapping, physical_paths, ctg):
        """
        Counts number of swap gates.

        Parameters:
        mapping (List[(string, int)]): Mapping from logical circuit to physical architecture.
        physical_paths (dict(int: List[(int, int)])): Shortest physical paths using Djikstra algorithm.
        ctg (List[edge(u, w, weight)]): Logical circuit.

        Returns:
        int: number of swap gates.
        """
        numswap = 0

        for edge in ctg:
            node1 = mapping[edge[0]]
            node2 = mapping[edge[1]]
            if len(physical_paths[node1][node2]) != 0:
                numswap += (len(physical_paths[node1][node2])) * 2

        return numswap
