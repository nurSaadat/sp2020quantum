
#%%
from qiskit import ClassicalRegister, QuantumRegister
from qiskit import QuantumCircuit,compiler, execute,IBMQ
from qiskit import Aer
from qiskit.tools.visualization import circuit_drawer
from qiskit.tools.visualization import plot_histogram
#from qiskit import register, available_backends, get_backend
from math import pi
#from qiskit.wrapper.jupyter import *
import matplotlib.pyplot as plt
import sys

from qiskit.tools.visualization import circuit_drawer
from parseRealization import *
get_ipython().run_line_magic('matplotlib', 'inline')

provider0 = IBMQ.load_account()
testDir="./tests/"


#%%

def quasmToMatlab(s):
    count = 0
    lines = s.split('\n')
    for line in lines:
        if line.startswith("x"):
            count = count + 1
            tokens = int(line.split(" ")[1].split("[")[1].split("]")[0])+1
            string = str(tokens)+" "+str(tokens)+" 0 "+str(pi)+" "+str(0)
            print(string)
        if line.startswith("swap"):
            count = count + 1
            tokens = line.split("[")
            index1 = int(tokens[1].split("]")[0])+1
            index2 = int(tokens[2].split("]")[0])+1
            string = str(index1)+" "+str(index2)+" 2 "+str(-10)+" "+str(0)
            print(string)
        if line.startswith("cx"):
            count = count + 1
            tokens = line.split("[")
            index1 = int(tokens[1].split("]")[0])+1
            index2 = int(tokens[2].split("]")[0])+1
            q = -15
            if index1>index2:
                q = -20
                t = index1
                index1 = index2
                index2 = t
            string = str(index1)+" "+str(index2)+" 2 "+str(q)+" "+str(0)
            print(string)
        if line.startswith("ry"):
            count = count + 1
            tokens = line.split("(")
            parameter = float(tokens[1].split(")")[0])
            index = int(tokens[1].split("[")[1].split("]")[0])+1
            string = str(index)+" "+str(index)+" 1 "+str(parameter)+" "+str(0)
            print(string)
        if line.startswith("rzz"):
            count = count + 1
            tokens = line.split("(")
            parameter = float(tokens[1].split(")")[0])
            tokenz = tokens[1].split("[")
            index1 = int(tokenz[1].split("]")[0])+1
            index2 = int(tokenz[2].split("]")[0])+1
            
            string = str(index1)+" "+str(index2)+" 2 "+str(parameter)+" "+str(0)
            print(string)
        if line.startswith("rz("):
            count = count + 1
            tokens = line.split("(")
            parameter = float(tokens[1].split(")")[0])
            index = int(tokens[1].split("[")[1].split("]")[0])+1
            string = str(index)+" "+str(index)+" 2 "+str(parameter)+" "+str(0)
            print(string)
        if line.startswith("rx"):
            count = count + 1
            tokens = line.split("(")
            parameter = float(tokens[1].split(")")[0])
            index = int(tokens[1].split("[")[1].split("]")[0])+1
            string = str(index)+" "+str(index)+" 0 "+str(parameter)+" "+str(0)
            print(string)
    print(count)


def testFromFile(fileName,details=0,drawPicture=0):
    ioClass = readCircuitInformation(fileName) 
    answers = ioClass.getKmap()
    errors=[]
  
    ioClass.readGatesFromFile(fileName)
    size = ioClass.getSize()
    print (ioClass.getKmap())
    error_count = 0
    backend_sim = Aer.get_backend('qasm_simulator')
    t = 0
    ctg = CircuitTransitionGraph()
    ctg.setSize(size)
    for i in range(0,len(answers)):
        qr,cr,qc = ioClass.createCircuitAndSetInput(i)
        qc,qr = ctg.readGatesFromIOClass(qr,qc,ioClass)
        qc.measure(qr,cr)
        if t == 0 and details == 1 and drawPicture == 1:
            circuit_drawer(qc).show()
            print(qc.qasm())
            t = 1
        qcirc = compiler.transpile(qc)
        qobj = compiler.assemble(qc,backend_sim)
        job_sim = backend_sim.run(qobj)
        stats_sim = job_sim.result().get_counts()
        if details==1:
            print(stats_sim)
        error = ioClass.checkOutputs(stats_sim,i)
        error_count = error_count+error
    #print(ctg)
    if error_count != 0 :
        print("FAILURE:",fileName)
    if details==1:
        #print(qc.qasm())
        #print(quasmToMatlab(qc.qasm()))
        print("Input:Received:Expected")
        for item in errors:
            print(item)
        print(answers)
        print("ERROR:",error_count)
    return error_count
            #plot_histogram(stats_sim)


#%%
#test not

testNames=["hwb6","hwb4_12","testToffoli5","parity","0410184","test00","ex1","testCVCVdag","ham3_28","miller","hwb4_52","testVCVC","3_17","test01","simpleSwap","swap1-2","swap1-3", "swap3-2","test1","testCVCV","simpleToffoli","hwb4_52_mod","toffoli"]
fails = 0
testNames = ["hwb6","hwb4_12","testToffoli5"]
for fileName in testNames:
    fileName = testDir + fileName 
    fails = fails + testFromFile(fileName,1,0)
if fails == 0:
    print("SUCCESS")
print(fails,len(testNames))
    

