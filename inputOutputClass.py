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
        self.ancilaSize =0

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
        if len(tokens)>0:
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
        if self.hasGarbage == 0:
            for release in counts.keys():
            #        print("The \"release object is\"",release)
                myString = flipTheString(release)
                print ("BEFOR THE Error occurred",str(number) ,"FLIPPED IS: ", myString ,", WHE GOT THIS:",release,"ExpectedAnswerIS",expectedAnswer)
                if self.ancilaSize!=0:
                    release = release[self.ancilaSize:]
                myString = flipTheString(release)
                #to cut away ancila!
                print ("BEFOR THE Error occurred without ANCILA",str(number) ,"FLIPPED IS: ", myString ,", WHE GOT THIS:",release,"ExpectedAnswerIS",expectedAnswer)
                if myString != expectedAnswer:
                    print ("Error occurred",str(number) ,":", myString ,":",release)
                    return 1
        else:
            foundErrors = 0
            for release in counts.keys():
                myString = flipTheString(release)
                myStringIter = 0
                for i in range (0,len(self.garbage)):
                    if self.garbage[i]=="-":
                        if myString[myStringIter]!=expectedAnswer[myStringIter]:
                            foundErrors = foundErrors+1
                        myStringIter=myStringIter+1
            if foundErrors!=0:
                return 1
        return 0
    #returns quantum register and quantum circuit initializing to @param state (matching the pla file)
    def createCircuitAndSetInput(self,number):
        size = self.size
        size = size + self.ancilaSize
        #print("Size is",size)
        qr = QuantumRegister(size)
        cr = ClassicalRegister(size)
        qc = QuantumCircuit(qr,cr)
        if self.hasConstantInputs == 0:
            formatString = "{:0"+str(size)+"b}"
            myString = formatString.format(number)
            #print("My string is: ",myString,", size is ",size)
            print("j is:","myString",myString)
            for j in range(self.ancilaSize,size):
                
                if myString[j]=="1":
                    qc.x(qr[j-self.ancilaSize])
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
            #print("Reached here in preparation of inputs!!!, the inputList is",inputList)
            for j in range(0,size):
                print("j is:",j,"InputList",inputList[j])
                if inputList[j]=="1":
                    qc.x(qr[j])
        elif self.hasGarbage == 1 and self.hasConstantInputs==1:
            inputList = []
            theNumber = list(self.kMap.keys())[number]
            i = 0 
            j = 0
           # print("Constant field is:",self.constants)
           # print("Length of constants field is:",len(self.constants))
            while i < len(self.constants):
                if self.constants[i]!="-":
                    inputList.append(self.constants[i])
                else:
                    inputList.append(theNumber[j])
                    j = j + 1
                i =  i + 1   
            #print("Reached here in preparation of inputs!!!, the inputList is",inputList)
            for j in range(0,size):
                if inputList[j]=="1":
                    qc.x(qr[j])
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
                self.checkToffoli(lineRead)

    def checkToffoli(self,lineRead):
        tokens = lineRead.split(" ", 1)
        #print(tokens)
        little_token1 = tokens[0][0]
        if little_token1!="t":
            return
        little_token2 = tokens[0][1]
        if little_token1=="t" and int(little_token2) > 3:
            self.ancilaSize = int(little_token2)-3 


    def getLines(self):
        return self.lines



