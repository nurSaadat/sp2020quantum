from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute
from CircuitTransitionGraph import *
from math import pi
import numpy as np

class InputOutputClass:
    def __init__(self,ctg):
        self.ctg = ctg
        self.kMap = {}
        self.hasConstantInputs = 0
        self.hasGarbage = 0
        self.hasConstantInputs = 0


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
        else:
            k = 15
            

    def getKmap(self):
        return self.kMap

    def readKmapFromFile(self,fname):
        print("hi")
        with open(fname, 'r') as f:
            lines = f.readlines()
        print(lines)
        for lineRead in lines:
            lineRead=lineRead.replace('\n', '')
            tokens = lineRead.split()
            if 0 == lineRead.startswith("#") :
                if 0==lineRead.startswith("."):
                    self.kMap[tokens[0]]=tokens[1]
                    print(tokens[1])



