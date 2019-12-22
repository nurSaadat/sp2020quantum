#!/usr/bin/env python
# coding: utf-8
# In[1]:

#%load_ext autoreload
#%autoreload 2

from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit, execute,IBMQ
from qiskit import BasicAer
from qiskit.tools.visualization import circuit_drawer
from qiskit.tools.visualization import plot_histogram
from qiskit.providers.ibmq import least_busy
from math import pi
from qiskit.transpiler.layout import Layout as Ibmlayout
from qiskit.compiler import transpile
from qiskit.compiler import assemble
import matplotlib.pyplot as plt
import sys
from qiskit.tools.visualization import circuit_drawer
from parseRealization import *
from copy import deepcopy
#get_ipython().run_line_magic('matplotlib', 'inline')
testDir="./tests/"
# In[2]:
IBMQ.load_account()

# In[2]:


#select a backend
provider = IBMQ.get_provider(group='open')

#print(available)
#least_busy = BasicAer.get_backend('qasm_simulator')
least_busy = provider.get_backend('ibmq_16_melbourne')
couplingMap = least_busy.configuration().coupling_map
print(couplingMap,"its length:",len(couplingMap))
qubitsSize = least_busy.configuration().n_qubits


# In[3]:


def prepareIBMQLayout(qReg,layout,debug = False):
    ibmLayout = {}
    if True == debug:
        print("You've entered the function that generates an IBMQ layout", end ='')
        print(", current quantum register is:")
        print(qReg)
        print (" , current layout is")
        print(layout)
    for i in range(0,len(layout)):
        if True == debug:
            print ("Layout item is",i)
        logical = ord(layout[chr(i+ord("a"))])-ord("a")
        #quantum register
        physical = qReg[i]
        #Mapping of physical to logical qubit
        ibmLayout[physical]=logical
    #print("tempDictionary",ibmLayout)
    #print("items are",ibmLayout.items())
    if True == debug:
        print("Generated IBM layout is:")
        print(ibmLayout)
    return ibmLayout

def bigFunction(fileName,maxEpoch = 5,debug = False):
    #input and output PLA
    ioClass = readCircuitInformation(fileName) 
    #Mao input key to output
    answers = ioClass.getKmap()
    size = ioClass.getSize()
    #get the gates Real
    ioClass.readGatesFromFile(fileName)


    backend_sim = BasicAer.get_backend('qasm_simulator')
    error_count = 0
    #Empty CTG    
    ctg = CircuitTransitionGraph()
    #Read couplings into alphabetical representation
    tempStuff = ctg.transformCoupling(couplingMap,qubitsSize)
    if True == debug:
        print("The prepared coupling is:",tempStuff,len(tempStuff))
    ctg.setSize(size)
   
    leastCost = 2000000
    defaultIBMCost = 100000
    finalAnswer = []
    finalLayout = []
    costHistory =[]
    ibmCostHistory = []
    for i in range(0,1):
        epoch = 0
        #This part corresponds for part of experiment without minimal or no changes
        while epoch < maxEpoch:
            print("Epoch number:",epoch)
            if True == debug:
                print("Current layout of ctg is:",ctg.layout)
            #Copy the mapping of logical to physical, here it is a to a, b to b, etc    
            tempLayout = deepcopy(ctg.layout)
            #create empty circuit and create the input by logic circuit
            qr,cr,qc = ioClass.createCircuitAndSetInput(i,qubitsSize)
            #Map circuit qr to IBM and under constraints of qubit map tempLayout
            ibmLayout = prepareIBMQLayout(qr,tempLayout)
            #Fill the qr circuit
            qc,qr = ctg.readGatesFromIOClass(qr,qc, ioClass)
            if True == debug:
                print("LINES AFTER WE've just read them",ctg.lines)
            if epoch==0:
                #evaluate default layout
                defaultIBMCost = measureFidelityWithoutChanges(qr,cr,qc)
            #Fixing the circuit if any problems are detected    
            ctg = fixTheStuff(ctg,debug)
            if True == debug:
                print("LINES AFTER FIXING",ctg.lines)
            #This one needs to comply with changes you did
            #qc,qr = ctg.readFixedGatesFromCtg(qr,qc)
            #Create a new empty circuit and set inputs
            qr,cr,qc = ioClass.createCircuitAndSetInput(i,qubitsSize)
            #Red repaired gates - no idea why
            qc,qr = ctg.readFixedGatesFromCtg(qr,qc)
            if True == debug:
                print("LINES AFTER READING FIXED GATES FROM CTG",ctg.lines)
            #Map circuit qr to IBM and under constraints of qubit map tempLayout
            ibmLayout = prepareIBMQLayout(qr,tempLayout)
            #Compile and evaluate cost of the fixed circuit
            tempCost = compileToSeeCost(qr,cr,qc,ioClass,ibmLayout,i)

            ibmCostHistory.append(tempCost)
            costHistory.append(len(ctg.lines))
            print("Epoch "+str(epoch)+", cost history is:",tempCost)
            if tempCost < leastCost:
                finalAnswer = deepcopy(ctg.lines)
                finalLayout = deepcopy(tempLayout)
                leastCost = tempCost
            #Verify the logical correctness
            measureToVerifyOutputWtihChanges(ctg,ioClass,tempLayout,i,epoch)
            #Modifies the mapping from logical to physical
            ctg.layOutQubits()
            epoch = epoch+1
    for i in range(0,len(costHistory)):
        for j in range(0,len(costHistory)):
            if costHistory[i] < costHistory[j]:
                tempI = ibmCostHistory[j]
                temp = costHistory[j]
                costHistory[j]=costHistory[i]
                ibmCostHistory[j]=ibmCostHistory[i]
                costHistory[i] = temp
                ibmCostHistory[i] = tempI
    print("Default IBM cost is:",defaultIBMCost)
    print("FinalAnswer is:", finalAnswer)
    print("FinalAnswer finalLayout:", finalLayout)
    print("FinalAnswer cost is:",leastCost)
    print("CostHistory is:",costHistory)
    print("IBMCostHistory is:",ibmCostHistory)   
   
   # plt.plot(ibmCostHistory,costHistory)

    
def fixTheStuff(ctg,debug=False):
    if True == debug:
        print("Missing connections are",ctg.getMissingConnections())
    else:
        #returns missing connections that are missing in physical layout
        #changes state of CTG
        ctg.getMissingConnections()
    #This one to fix the changes... fixthemissingedges connects stuff around. did not test though
    #Brings the missing edges to LNN
    ctg.fixMissingEdges(debug)
    #print("FIxing the stuff")
    return ctg


def  compileToSeeCost(qr,cr,qc,ioClass,ibmLayout,i):
    #least_busy = BasicAer.get_backend('qasm_simulator')
    qc.measure(qr,cr)
    #transforms logic gates to qasm assembly
    #Bug about least_busy 
    qcircuit = transpile(qc,least_busy,initial_layout=ibmLayout,pass_manager=None)
    #prepares executable from qasm
    qobj = assemble(qcircuit)
    #print(qobj.experiments[0].instructions)
    return len(qobj.experiments[0].instructions)
    
def measureFidelityWithoutChanges(qr,cr,qc,debug = False):
    #least_busy = BasicAer.get_backend('qasm_simulator')
    qc.measure(qr,cr)
    #Bug about least_busy 
    qcircuit = transpile(qc,least_busy,initial_layout=None,pass_manager=None,optimization_level=3)
    outputName = str(fileName)+"IBM input"
    pictureName ="./outputs/pictures/"+ outputName+".png"
    textName = "./outputs/text/"+outputName+".txt"
    draw = False
    if True == draw:
        qc.draw(filename=pictureName,output="latex")
    f= open(textName,"w+")
    f.write(qcircuit.qasm())
    f.close
 
    qobj = assemble(qcircuit)
    if True == debug:
        #Prints all circuits
        print(len(qobj.experiments))
    #This line provides print of the compiled circuit qasm
    #print("Length of IBM compiled circuit is:",len(qobj.experiments[0].header.as_dict()["compiled_circuit_qasm"]))
    return len(qobj.experiments[0].instructions)
#This needs to be implemented    
def measureToVerifyOutputWtihChanges(ctg,ioClass,tempLayout,i,epoch,debug = True):
    if True == debug:
        print ("Hello from test routine")
    #target input outputs mapping
    answers = ioClass.getKmap()
    size = ioClass.getSize()
    error_count = 0
    #This should be a local variable otherwise changes are for everyone
    least_busy = BasicAer.get_backend('qasm_simulator')
    if True == debug:
        print ("Length of answers is:",len(answers))
    #for every single output input pair
    for i in range(0,len(answers)):
        if True ==debug:
            print("Testing input ",i)
        qr,cr,qc = ioClass.createCircuitAndSetInput(i,qubitsSize)
        qc,qr = ctg.readFixedGatesFromCtg(qr,qc)
        if True == debug:
            print("LINES AFTER READING FIXED GATES FROM CTG",ctg.lines)
        ibmLayout = prepareIBMQLayout(qr,tempLayout) 
        qc.measure(qr,cr)
        qc = transpile(qc,least_busy,initial_layout=ibmLayout)
        if True == debug:
            outputName = str(fileName)+"epoch"+str(epoch)+"input"+str(i)
            pictureName ="./outputs/pictures/"+ outputName+".png"
            textName = "./outputs/text/"+outputName+".txt"
            draw = False
            if True == draw:
                qc.draw(filename=pictureName,output="latex")
            f= open(textName,"w+")
            f.write(qc.qasm())
            f.close
        qobj = assemble(qc,shots=20)
        job = execute(qc,least_busy)
        stats_sim = job.result().get_counts()
        error = ioClass.checkOutputs(stats_sim,i)
        error_count = error_count+error

    if error != 0 :
        print("ERROR APPEARED on epoch",epoch)
        raise SystemError
    else:
        print ("Epoch", epoch,": all tests passed")
    #plot_histogram(result.get_counts())


# In[4]:
passes = ["hwb4_52","3_17","ex1","testCVCV","toffoli","miller","fredkin_3","ex1","toffoli"]
doesNotPass = ["0410184","decod24-v_142","parity","graycode6_47","testCVCV","hwb4_52","3_17","decod24-v_142","ex1","toffoli_double_2","testCVCV",]
for elem in passes:
#for elem in doesNotPass:
    fileName = elem
    fullFileName = testDir+fileName
    bigFunction(fullFileName,maxEpoch=10,debug=False)


# %%
