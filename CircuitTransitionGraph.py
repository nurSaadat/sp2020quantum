from math import pi
class CircuitTransitionGraph:
    def __init__(self):
        self.weights = {}
        self.sk = []
        self.lines = []
        self.v = set()
        self.paths = dict()
        self.trace = []
        self.weightsForPath = []
        self.bestPossibleEdge =[]
        self.found = 0
        self.cost = 0
        self.highestConnectivityNodes = []
        self.coupling = {}
        self.QuantumComputerCoupling = []
        self.size = 0

    def getSize(self):
        return self.size
        
    def modifyWeights(self,first,second):
        self.v.add(first)
        self.v.add(second)
        if second < first:
            temp = first
            first = second
            second = temp
        key = str(first)+str(second)
        self.weights[key]=self.weights.get(key,0)+1
        self.sk.append(key)

    def getMissingConnections(self):
        self.notMatching = []
        t = self.coupling
        print("Self skeleton is",self.sk)
        for i in self.sk:
            if (t.get(i[0])!= None):
                if (i[1] not in t.get(i[0])):
                    tPair = [i[0],i[1]]
                    self.notMatching.append(tPair)
            else:
                tPair = [i[0],i[1]]
                self.notMatching.append(tPair)
        return self.notMatching

    def modifyWeightsOneQubit(self,only):
        self.v.add(only)
     
    def setSize(self,size):
        self.size = size

 #   def buildPaths(self):
  #      for i in self.sk:
   #         vFrom = i[0]
    #        self.paths[vFrom]=set()
     #   for i in self.sk:
      #      vFrom = i[0]
       #     vTo = i[1]
        #    pat=self.paths.get(vFrom)
         #   pat.add(vTo)
          #  self.paths[vFrom]=pat
#run an experiemnt and check noise
# run an experiment and swap with shit

#    def findNodesThatLeadToTo(self, listPiece):
 #       to = listPiece[1]
  #      possibleEdges = []
   #     for element in self.coupling:
    #        if to in self.coupling.get(element):
     #           possibleEdges.append( element)


      #  if element not in possibleEdges:
            #startRecursion
         #   return []

      #  return possibleEdges

    #def findNodesFromConnectedTo(self, listPiece):
     #   fro = listPiece[0]
      #  possibleNodes = []
       # for i in self.coupling.get(fro):
        #    possibleNodes.append(i)
        #return possibleNodes
    
    def edgeExist(self,a,b):
        if b in self.coupling.get(a):
            return 1
        else:
            return 0

   # def findConnectedToBoth(self,listFrom,listTo):
    #    possibleEdges = []
     #   for a in listFrom:
      #      for b in listTo:
       #         if self.edgeExist(a,b):
        #            possibleEdges.append([a,b])
        #        
        #return possibleEdges
    

    def selectLeastOccupied(self, smallList):
        minSize = len(smallList[0])
        myIndex = 0
        for element in smallList:
            if len(element)<minSize:
                minSize = len(element)
                myIndex = smallList.index(element)
        return smallList[myIndex]

    def findIndexOfTheGateSkeleton(self,notMatching):
        inn = 0
        for line in self.lines:
            tokens = line.split(" ",1)
            #todo extend the list with the others
            if tokens[0]=="t2": 
                variables=tokens[1].split()
                print(variables,notMatching)
                if self.checkSkeletonEquivalence(variables,notMatching)==1:
                    return inn
                    print("RETURN DID NOT WORK")
            inn = inn + 1
        return inn


    def checkSkeletonEquivalence(self, g1,g2):
        g2.sort()
        g1.sort()
        if g1[0]==g2[0]:
            if g1[1]==g2[1]:
                return 1
        return 0

    def whatToReplace(self,item1,item2):
        if (item1[0] == item2[0]):
            return [item1[1],item2[1]]
        else:
            return [item1[0],item2[0]]

    def rebuildGate(self,replaceTo,index):
        lineToCorrect = self.lines[index]
        tokens = lineToCorrect.split()
        where = tokens.index(replaceTo[0])
        tokens[where] = replaceTo[1]
        replacement = ""
        for element in tokens:
            if len(replacement) != 0:
                replacement = replacement+" "+element
            else:
                replacement = replacement+element
        self.lines[index] = replacement

    def surroundWithSwaps(self,index,replaceTo,thing):
        size = len(replaceTo)
        print("replaceTo",replaceTo)
        for i in range(size-2):
            swapString = "sw "+ replaceTo[i] + " " + replaceTo[i+1]
            print(swapString)
            self.lines.insert(index+i+1,swapString)
            self.weights
            self.lines.insert(index+i,swapString)
    
        print(thing)
        self.rebuildGate(thing,index+size-2)

    def fixTheSkeleton(self,element,replaceTo):
        skElement = str(element[0])+str(element[1])
        nskElement = str(replaceTo[0])+str(replaceTo[1])
        if self.sk.index(skElement):
            t = self.sk.index(skElement)
            self.sk[t] = nskElement
        print("fixed skeleton",self.sk)
            
    def fixMissingEdges(self):
        for element in self.coupling:
            print(element)
        for element in self.notMatching:
            print( "Paths to",element[0],element[1])
            self.findPath(element[0],element[1])
            
            self.getPathAndStuff()
            # Select first element record noise
            # Select second element record noise
            # Select .... elements record noise

            self.bestPossibleEdge = self.selectLeastOccupied(self.possiblePath)
            bestPossibleEdge = self.bestPossibleEdge
            #print("Hoy",bestPossibleEdge)
            #fix the possibilities: if the first is to , then insert the swap to from and the bestPossibleEdge
            lastPair = [bestPossibleEdge[len(bestPossibleEdge)-2],bestPossibleEdge[len(bestPossibleEdge)-1]]
            replaceTo =  self.whatToReplace(element,lastPair)
            ind = self.findIndexOfTheGateSkeleton(element)
            #print(ind)
            self.surroundWithSwaps(ind,bestPossibleEdge,replaceTo)
            self.fixTheSkeleton(element,replaceTo)
            #print("What to replace is:",replaceTo)

    def transformCoupling(self,maList):
        for element in maList:
            self.coupling[chr(element[0]+ord("a"))] = set()
            self.coupling[chr(element[1]+ord("a"))] = set()
        for element in maList:
            self.coupling[chr(element[0]+ord("a"))].add(chr(element[1]+ord("a")))
            self.coupling[chr(element[1]+ord("a"))].add(chr(element[0]+ord("a")))
        return self.coupling
          
    def findCurrentCost(self):
    	self.cost = 0
    	for element in self.weights:
    		self.cost = self.cost+element
    	print (self.cost)


    def findPath(self,current,vTo):
        self.trace = []
        self.weightsForPath = []
        self.found = 0
        self.possiblePath = []
        self.cost = 0
        self.findPathHelper(current,vTo,[current])
        for i in range(0,len(self.trace)-1):
            key = str(self.trace[i]) + str(self.trace[i+1])

    def getPathAndStuff(self):
        print("Trace is")
        print(self.possiblePath)
        return self.trace,self.weightsForPath

    def findHighestConnectivityNodesInCoupling(self):
        maximumConnections = 0
        maximumElementList = []
        for element in self.coupling:
            if len(self.coupling[element])>maximumConnections:
                maximumElementList = []
                maximumConnections = len(self.coupling[element])
                maximumElementList.append(element)
            elif len(self.coupling[element])==maximumConnections:
                maximumElementList = []
                maximumConnections = len(self.coupling[element])
                maximumElementList.append(element)
        self.highestConnectivityNodes = maximumElementList

   
    def setCoupling(self,maList):
        for element in self.coupling:
            key = str(chr(element[0]+ord("a")))+str(chr(element[1]+ord("a")))
        self.coupling.append(key)
        return self.coupling
        
    #The function is supposed to return reversed list of nodes
    #required to traverse to reach the vTo node from the 
    #current node

    def findPathHelper(self,current,vTo,trace):
        if current == vTo :
            self.possiblePath.append(trace)
            return
        #print(self.coupling.get(current))
        for i in self.coupling.get(current):
            element = str(i)
            if not (element in trace):
         #       print(i)
                #modify here to costs????
                t = trace.copy()
                if not (str(i) in t):
                    t.append(str(i))
                self.findPathHelper(i,vTo,t)
     
    def readGatesFromIOClass(self,qr,qc,ioClass):
        self.lines = ioClass.getLines()
        for lineRead in self.lines:
            tokens = lineRead.split(" ",1)
            if tokens[0]=="t3": 
                variables=tokens[1].split(" ")
                first = ord(variables[0][0])-ord('a')
                second = ord(variables[1][0])-ord('a')
                target = ord(variables[2][0])-ord('a')
                qc,qr = self.insertToffoliGate(qc,qr,first,second,target)
                #qc.ccx(qr[first],qr[second],qr[target])
            if tokens[0]=="v": 
                variables=tokens[1].split(" ")
                control = ord(variables[0][0])-ord('a')
                target = ord(variables[1][0])-ord('a')
                qc,qr = self.insertV(qc,qr,control,target)
            if tokens[0]=="v+":             
                variables=tokens[1].split(" ")
                control = ord(variables[0][0])-ord('a')
                target = ord(variables[1][0])-ord('a')
                qc,qr = self.insertVdag(qc,qr,control,target)
            if tokens[0]=="t2":             
                variables=tokens[1].split(" ")
                self.modifyWeights(variables[0][0],variables[1][0])
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
                qc,qr = self.insertSwaps(qc,qr,firstWire,secondWire)

       # print (ctg.getPathAndStuff())
        return qc,qr

       
    def readFixedGatesFromCtg(self,qr,qc):
            lines = self.lines
            for lineRead in lines:
                tokens = lineRead.split(" ",1)
                if tokens[0]=="t3": 
                    variables=tokens[1].split(" ")
                    first = ord(variables[0][0])-ord('a')
                    second = ord(variables[1][0])-ord('a')
                    target = ord(variables[2][0])-ord('a')
                    qc,qr = self.insertToffoliGate(qc,qr,first,second,target)
                    #qc.ccx(qr[first],qr[second],qr[target])
                if tokens[0]=="v": 
                    variables=tokens[1].split(" ")
                    control = ord(variables[0][0])-ord('a')
                    target = ord(variables[1][0])-ord('a')
                    qc,qr = self.insertV(qc,qr,control,target)
                if tokens[0]=="v+":             
                    variables=tokens[1].split(" ")
                    control = ord(variables[0][0])-ord('a')
                    target = ord(variables[1][0])-ord('a')
                    qc,qr = self.insertVdag(qc,qr,control,target)
                if tokens[0]=="t2":             
                    variables=tokens[1].split(" ")
                    self.modifyWeights(variables[0][0],variables[1][0])
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
                    qc,qr = self.insertSwaps(qc,qr,firstWire,secondWire)

           # print (ctg.getPathAndStuff())
            return qc,qr

    def resetCtg(self):
        self.weights = {}
        self.sk = []
        self.lines = []
        self.v = set()
        self.paths = dict()
        self.trace = []
        self.weightsForPath = []
        self.bestPossibleEdge =[]
        self.found = 0
        self.cost = 0
        self.highestConnectivityNodes = []
        self.coupling = {}
        self.size = 0


    def applySwap(self,qc,qr,first,second):
        qc.cx(qr[first],qr[second])
        qc.h(qr[first])
        qc.h(qr[second])
        qc.cx(qr[first],qr[second])
        qc.h(qr[first])
        qc.h(qr[second])
        qc.cx(qr[first],qr[second])
        return qc,qr
    #debugHere

    #TODO consider modifying weights bty multiple
    def insertSwaps(self,qc,qr,first,second):
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
            self.modifyWeights(k,k2)
            qc,qr = self.applySwap(qc,qr,i,i+1)
        return qc,qr

    #this function applies controlled v gate to the circuit. the target MUST be control + 1
    def applyV(self,qc,qr,control,target):
        if target - 1 != control:
            print ("The self.insertV function should be applied instead applyV")
            exit(0)

        qc.tdg(qr[control])
        qc.h(qr[target])
        qc.cx(qr[target],qr[control])
        qc.t(qr[control])
        qc.tdg(qr[target])
        qc.cx(qr[target],qr[control])
        qc.h(qr[target])
        self.modifyWeights(chr(ord("a")+target),chr(ord("a")+control))
        self.modifyWeights(chr(ord("a")+target),chr(ord("a")+control))
        return qc, qr

    def applyVdag(self,qc,qr,control,target):
        if target - 1 != control:
            print ("The self.insertV function should be applied instead applyV")
            exit(0)
        qc.h(qr[target])
        qc.cx(qr[target],qr[control])           
        qc.t(qr[target])  
        qc.tdg(qr[control])        
        qc.cx(qr[target],qr[control])
        qc.h(qr[target])
        qc.t(qr[control])



        return qc, qr

    def insertV(self,qc,qr,control,target):
        second = target - 1
        first = control
        maximum = target
        if target<control:
            first = target
            second = control
            maximum = control
        qc,qr=self.insertSwaps(qc,qr,first,second)
        qc,qr=self.applyV(qc,qr,maximum-1,maximum)
        qc,qr=self.insertSwaps(qc,qr,second,first)
        return qc,qr

    def insertVdag(self,qc,qr,control,target):
        second = target - 1
        first = control
        maximum = target
        if target<control:
            first = target
            second = control
            maximum = control
        qc,qr=self.insertSwaps(qc,qr,first,second)
        qc,qr=self.applyVdag(qc,qr,maximum-1,maximum)
        qc,qr=self.insertSwaps(qc,qr,second,first)
        return qc,qr


    def applyToffoliGate(self,qc,qr,first,second,third):
        qc,qr=self.insertSwaps(qc,qr,first,second)
        qc,qr=self.insertV(qc,qr,second,third)
        qc,qr=self.insertSwaps(qc,qr,first,second)
        qc,qr=self.insertV(qc,qr,second,third)
        qc.cx(qr[first],qr[second])
        self.modifyWeights(chr(ord("a")+first),chr(ord("a")+second))
        qc,qr=self.insertVdag(qc,qr,second,third)
        qc.cx(qr[first],qr[second])
        self.modifyWeights(chr(ord("a")+first),chr(ord("a")+second))
        return qc,qr


    #TEST THOROUGHLY
    def insertToffoliGate(self,qc,qr,first,second,target):
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
        self.insertSwaps(qc,qr,target,maximum)    
        self.insertSwaps(qc,qr,second,maximum-1)
        self.insertSwaps(qc,qr,first,maximum-2)
        qc,qr =  self.applyToffoliGate(qc,qr,maximum-2,maximum-1,maximum)
        self.insertSwaps(qc,qr,maximum-2,first)
        self.insertSwaps(qc,qr,maximum-1,second)
        self.insertSwaps(qc,qr,maximum,target)  

        return qc,qr




           
    def __str__(self):
        return "Weights are:"+str(self.weights)+", skeleton is:"+str(self.sk)+", vertices are"+str(self.v)+", paths are "+str(self.paths)+",latest weight are"+str(self.weightsForPath)