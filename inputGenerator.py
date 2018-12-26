from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute
from CircuitTransitionGraph import *
from math import pi
import numpy as np

class InputOutputClass:
    def __init__(self,ctg):
        self.ctg = ctg


    def neededOrNot(self):
        self.inputs = list()
        size = ctg.getSize()
        expandedSize = pow(2,size)   
        for i in range(0,expandedSize):
            self.inputs.add(0)


    def setSize(self,size):
        self.size = size

    #returns quantum register and quantum circuit initializing to @param state (matching the pla file)
    def createCircuitAndSetInput(self,number):
        if self.ctg.hasConstantInputs != 0:
        #TODO implement garbage
            k = 42
        else
            


    def verifyOutput(self)

