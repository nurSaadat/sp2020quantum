from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute
from CircuitTransitionGraph import *
from math import pi
import numpy as np

#works only if variable names are single characters in the alphabet)
def readCircuitInformation(fname):
    global ctg
    global ioClass
    global testDir
    fileName1 = testDir+fileName + ".real"
    fileName2 = testDir+fileName + ".pla"
    print(filename2)
    ctg = CircuitTransitionGraph()
    ioClass = InputOutputClass(ctg)
    size = -1
    # block opens file and read all lines
    with open(fname, 'r') as f:
        lines = f.readlines()

    #iterating through each line of code
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]==".numvars":
            size =int( tokens[1])
            ctg.setSize(size)
            ioClass.setSize(size)
        if tokens[0]==".inputs":
            for i in range(1,len(tokens)):
                if isDigit(tokens[i]):
                    ctg.hasConstantInputs = 1

    return size 




def applySwap(qc,qr,first,second):
	qc.cx(qr[first],qr[second])
	qc.h(qr[first])
	qc.h(qr[second])
	qc.cx(qr[first],qr[second])
	qc.h(qr[first])
	qc.h(qr[second])
	qc.cx(qr[first],qr[second])
	return qc,qr
#debugHere
def insertSwaps(qc,qr,first,second):
    global ctg
    t =[]
    if first == second:
        return qc,qr
    if second<first:
        for k in range(second,first):
            t.insert(0,k)
    else:
        t = range(first,second)
        
    for i in t:
        k = chr(i+ord('a'))
        k2 = chr(i+ord('a')+1)
        ctg.modifyWeights(k,k2)
        qc,qr = applySwap(qc,qr,i,i+1)
    return qc,qr

#this function applies controlled v gate to the circuit. the target MUST be control + 1
def applyV(qc,qr,control,target):
	global ctg
	if target - 1 != control:
		print ("The insertV function should be applied instead applyV")
		exit(0)
	qc.ry(pi/2,qr[target]);
	qc.rz(pi/4,qr[control]);
	qc.rz(pi/4,qr[target]);
	qc.rzz(-pi/4,qr[control],qr[target]);
	ctg.modifyWeights(chr(ord("a")+control),chr(ord("a")+target))
	qc.ry(-pi/2,qr[target]);
	return qc, qr

def applyVdag(qc,qr,control,target):
	global ctg
	if target - 1 != control:
		print ("The insertV function should be applied instead applyV")
		exit(0)
	qc.ry(-pi/2,qr[target]);
	qc.rzz(-pi/4,qr[control],qr[target]);
	ctg.modifyWeights(chr(ord("a")+control),chr(ord("a")+target))
	qc.rz(pi/4,qr[target]);
	qc.rz(pi/4,qr[control]);
	qc.ry(pi/2,qr[target]);
	return qc, qr;

def insertV(qc,qr,control,target):
	second = target - 1
	first = control
	maximum = target
	if target<control:
		first = target
		second = control
		maximum = control
	qc,qr=insertSwaps(qc,qr,first,second)
	qc,qr=applyV(qc,qr,maximum-1,maximum)
	qc,qr=insertSwaps(qc,qr,second,first)
	return qc,qr

def insertVdag(qc,qr,control,target):
	second = target - 1
	first = control
	maximum = target
	if target<control:
		first = target
		second = control
		maximum = control
	qc,qr=insertSwaps(qc,qr,first,second)
	qc,qr=applyVdag(qc,qr,maximum-1,maximum)
	qc,qr=insertSwaps(qc,qr,second,first)
	return qc,qr


def applyToffoliGate(qc,qr,first,second,third):
	global ctg
	qc,qr=insertSwaps(qc,qr,first,second)
	qc,qr=insertV(qc,qr,second,third)
	qc,qr=insertSwaps(qc,qr,first,second)
	qc,qr=insertV(qc,qr,second,third)
	qc.cx(qr[first],qr[second])
	ctg.modifyWeights(chr(ord("a")+first),chr(ord("a")+second))
	qc,qr=insertVdag(qc,qr,second,third)
	qc.cx(qr[first],qr[second])
	ctg.modifyWeights(chr(ord("a")+first),chr(ord("a")+second))
	return qc,qr


#TEST THOROUGHLY
def insertToffoliGate(qc,qr,first,second,target):
    myList = [first,second,target]
    myList.sort()
    maximum = myList[2]
    pos = myList.index(target)

    if pos == 0:
    	first = myList[1]-1
    	second = myList[2]-1
    if pos == 1:
    	first = myList[0]
    	second = myList[2]-1
    if pos == 2:
    	first = myList[0]
    	second = myList[1]
    insertSwaps(qc,qr,target,maximum)    
    insertSwaps(qc,qr,second,maximum-1)
    insertSwaps(qc,qr,first,maximum-2)
    qc,qr =  applyToffoliGate(qc,qr,maximum-2,maximum-1,maximum)
    insertSwaps(qc,qr,maximum-2,first)
    insertSwaps(qc,qr,maximum-1,second)
    insertSwaps(qc,qr,maximum,target)  

    return qc,qr


def readGatesFromCtg(qc,qr,ctg):
    lines = ctg.getLines()
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]=="t3": 
            variables=tokens[1].split(" ")
            first = ord(variables[0][0])-ord('a')
            second = ord(variables[1][0])-ord('a')
            target = ord(variables[2][0])-ord('a')
            qc,qr = insertToffoliGate(qc,qr,first,second,target)
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


def readGatesFromCtg(qc,qr,ctg):
    lines = ctg.getLines()
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]=="t3": 
            variables=tokens[1].split(" ")
            first = ord(variables[0][0])-ord('a')
            second = ord(variables[1][0])-ord('a')
            target = ord(variables[2][0])-ord('a')
            #qc.ccx(qr[first],qr[second],qr[target])
            qc,qr = insertToffoliGate(qc,qr,first,second,target)
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
def readGatesFromFile(fname,ctg):
    with open(fname, 'r') as f:
        lines = f.readlines()
    for lineRead in lines:
        if not (lineRead.startswith("#") or lineRead.startswith(".") or lineRead.startswith("\n")):
            ctg.storeLine(lineRead)
        tokens = lineRead.split(" ",1)
        if tokens[0]=="t3": 
            variables=tokens[1].split(" ")
            first = ord(variables[0][0])-ord('a')
            second = ord(variables[1][0])-ord('a')
            target = ord(variables[2][0])-ord('a')
            #qc,qr = insertToffoliGate(qc,qr,first,second,target)
           # qc.ccx(qr[first],qr[second],qr[target])
        if tokens[0]=="v": 
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            #qc,qr = insertV(qc,qr,control,target)
        if tokens[0]=="v+":             
            variables=tokens[1].split(" ")
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            #qc,qr = insertVdag(qc,qr,control,target)
        if tokens[0]=="t2":             
            variables=tokens[1].split(" ")
            ctg.modifyWeights(variables[0][0],variables[1][0])
            control = ord(variables[0][0])-ord('a')
            target = ord(variables[1][0])-ord('a')
            #qc.cx(qr[control],qr[target])

        if tokens[0]=="x":             
            variables=tokens[1].split(" ")
            t = ord(variables[0][0])-ord('a')
            #qc.x(qr[t])
        if tokens[0]=="sw":             
            variables=tokens[1].split(" ")
            firstWire = ord(variables[0][0])-ord('a')
            secondWire = ord(variables[1][0])-ord('a')
            #qc,qr = insertSwaps(qc,qr,firstWire,secondWire)
    #ctg.buildPaths()
    return ctg
  #  ctg.findPath("a","e")
   # print (ctg.getPathAndStuff())
   # return qc,qr,ctg

#TODO remove 
def readSizeFromFile(fname):
    global ctg
    ctg = CircuitTransitionGraph()
    size = -1
    with open(fname, 'r') as f:
        lines = f.readlines()
    for lineRead in lines:
        tokens = lineRead.split(" ",1)
        if tokens[0]==".numvars":
            size =int( tokens[1])
            ctg.setSize(size)
    return size 


#may need to return transpose
def getMatrixFromKmap(Stringz,size):
    size =pow(2,size)
    myArr = np.zeros((size,size))
    for i in Stringz:
        myArr[int(i,2)][int(Stringz[i],2)]=1
    return myArr

def readKmapFromFile(fname):
    with open(fname, 'r') as f:
        lines = f.readlines()
    s = {}
    for lineRead in lines:
        lineRead=lineRead.replace('\n', '')
        tokens = lineRead.split()
        if 0 == lineRead.startswith("#") :
            if 0==lineRead.startswith("."):
                s[tokens[0]]=tokens[1]
    return s