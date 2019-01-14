from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute
from CircuitTransitionGraph import *
from math import pi
import numpy as np
def flipTheString(s):
    myString=""
    length = len(s)
    for it in range(0,length):
        myString=myString+s[length-1-it]
    return myString

class InputOutputClass:
    def __init__(self):
        self.kMap = {}
        self.lines = []
        self.hasGarbage = 0
        self.hasConstantInputs = 0
        self.constants = ""
        self.garbage = ""
        self.inputs = ""
        self.outputs = ""

    def setConstants(self,line):
        print("The constants are set to",line)
        tokens = line.split()
        self.constants = tokens[1] 


    def setOutputs(self,line):
        self.outputs = line

    def setInputs(self,line):
        self.inputs = line
    
    def setGarbage(self,line):
        self.garbage = line

    def getSize(self):
        return self.size

    def processConstantInputs(self):
        inputTokens = self.inputs.split()
        outputTokens = self.outputs.split()
        inputSize = len(inputTokens)
        outputSize = len(outputTokens)
        if inputSize == outputSize:
            for i in range(1,inputSize):
                if inputTokens[i]!=outputTokens[i]:
                    self.hasConstantInputs = 1
        else:
            self.hasConstantInputs = 1



    def processGarbage(self):
        tokens = self.garbage.split()
        if tokens[1]:
            for t in tokens[1]:
                if not t == "-":
                    self.hasGarbage = 1
        else:
            self.hasGarbage = 0

    def determineInputs(self):
        self.processGarbage()
        self.processConstantInputs()
        if self.hasGarbage == 1:
            print("The circuit has garbage lines in it or file parsed incorrectly, check ioclass")
        else:
            print("The circuit has no garbage lines in it or file parsed incorrectly, check ioclass")
        if self.hasConstantInputs == 1:
            print("The circuit has constant inputs in it or file parsed incorrectly, check ioclass")
        else:
            print("The circuit has no constant inputs lines in it or file parsed incorrectly, check ioclass")
  


    def setSize(self,size):
        self.size = size

    # The function is supposed to return one if there is an error or 
    # return zero if there's not
    # @param2 is the results of execution
    # @param3 is the index of the element in the k-map
    # Assumption: The function works if the values order for dict in python is preserved!
    def checkOutputs(self,counts,number):
        expectedAnswer = list(self.kMap.values())[number]
        
        #print("The expected answer is",expectedAnswer)
        #print("The actual answer is",counts)
        
        for release in counts.keys():
        #        print("The \"release object is\"",release)
         
                myString = flipTheString(release)
                if myString != expectedAnswer:
                    print ("Error occurred",str(number) ,":", myString ,":",release)
                    return 1

        return 0
    #returns quantum register and quantum circuit initializing to @param state (matching the pla file)
    def createCircuitAndSetInput(self,number):
        size = self.size
        #print("Size is",size)
        qr = QuantumRegister(size)
        cr = ClassicalRegister(size)
        qc = QuantumCircuit(qr,cr)
        if self.hasConstantInputs == 0:
            formatString = "{:0"+str(size)+"b}"
            myString = formatString.format(number)
            #print("My string is: ",myString,", size is ",size)
            for j in range(0,size):
                if myString[j]=="1":
                    qc.x(qr[j])
        elif self.hasGarbage == 1 and self.hasConstantInputs==0:
            k = 42
        elif self.hasGarbage == 0 and self.hasConstantInputs==1:
            inputList = []
            theNumber = list(self.kMap.keys())[number]
            i = 0 
            j = 0
            print("Constant field is:",self.constants)
            print("Length of constants field is:",len(self.constants))
            while i < len(self.constants):
                if self.constants[i]!="-":
                    inputList.append(self.constants[i])
                else:
                    inputList.append(theNumber[j])
                    j = j + 1
                i =  i + 1   
            print("Reached here in preparation of inputs!!!, the inputList is",inputList)
            for j in range(0,size):
                if inputList[j]=="1":
                    qc.x(qr[j])
        elif self.hasGarbage == 1 and self.hasConstantInputs==1:
            k = 15
        return qr,cr,qc
            

    def getKmap(self):
        return self.kMap

    def readKmapFromFile(self,fname):
        with open(fname, 'r') as f:
            lines = f.readlines()
        for lineRead in lines:
            lineRead=lineRead.replace('\n', '')
            tokens = lineRead.split()
            if 0 == lineRead.startswith("#") :
                if 0==lineRead.startswith("."):
                    self.kMap[tokens[0]]=tokens[1]



    def readGatesFromFile(self,fname):
        fname = fname + ".real"
        with open(fname, 'r') as f:
            lines = f.readlines()
        for lineRead in lines:
            if not (lineRead.startswith("#") or lineRead.startswith(".") or lineRead.startswith("\n")):
                self.lines.append(lineRead)


    def getLines(self):
        return self.lines


