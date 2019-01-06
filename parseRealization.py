from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute
from CircuitTransitionGraph import *
from inputOutputClass import *
from math import pi
import numpy as np

#works only if variable names are single characters in the alphabet)
def readCircuitInformation(fname):
    fileName1 = fname + ".real"
    fileName2 = fname + ".pla"
    print(fileName2)
    ioClass = InputOutputClass()
    size = -1
    #block opens file and read all lines
    with open(fileName1, 'r') as f:
        lines = f.readlines()
  #  iterating through each line of code
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]==".numvars":
            size =int( tokens[1])
            ioClass.setSize(size)
        if tokens[0]==".inputs":
            ioClass.setInputs(lineRead)
        if tokens[0]==".constants":
            ioClass.setConstants(lineRead)
        if tokens[0]==".outputs":
            ioClass.setOutputs(lineRead)
        if tokens[0]==".garbage":
            ioClass.setGarbage(lineRead)
    ioClass.determineInputs()
    ioClass.readKmapFromFile(fileName2)
    return ioClass
    #return size 



def readGatesFromCtgNoMod(qc,qr,ctg):
    lines = ctg.getLines()
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]=="t3": 
            variables=tokens[1].split(" ")
            first = ord(variables[0][0])-ord('a')
            second = ord(variables[1][0])-ord('a')
            target = ord(variables[2][0])-ord('a')
            qc.ccx(qr[first],qr[second],qr[target])
            #qc.ccx(qr[first],qr[second],qr[target])
        if tokens[0]=="v": 
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            qc,qr = insertV(qc,qr,control,target)
        if tokens[0]=="v+":             
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            qc,qr = insertVdag(qc,qr,control,target)
        if tokens[0]=="t2":             
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            qc.cx(qr[control],qr[target])
        if tokens[0]=="t1":             
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            qc.x(qr[control])
        if tokens[0]=="x":             
            variables=tokens[1].split(" ")
            t = ord(variables[0][0])-ord('a')
            qc.x(qr[t])
        if tokens[0]=="sw":             
            variables=tokens[1].split(" ")
            firstWire = ord(variables[0][0])-ord('a')
            secondWire = ord(variables[1][0])-ord('a')
            qc,qr = insertSwaps(qc,qr,firstWire,secondWire)

   # print (ctg.getPathAndStuff())
    return qc,qr


#may need to return transpose
def getMatrixFromKmap(Stringz,size):
    size =pow(2,size)
    myArr = np.zeros((size,size))
    for i in Stringz:
        myArr[int(i,2)][int(Stringz[i],2)]=1
    return myArr

