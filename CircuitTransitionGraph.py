from math import pi
import collections
class CircuitTransitionGraph:
    def __init__(self):
        self.weights = {}
        self.qubitConnectionsCount=[]
        self.sk = []
        self.lines = []
        self.v = set()
        self.paths = dict()
        self.trace = []
        self.weightsForPath = []
        self.bestPossibleEdge =[]
        self.found = 0
        self.layout = {}
        self.cost = 0
        self.couplingAsList = []
        self.inverseLayout = {}
        self.highestConnectivityNodes = []
        self.coupling = {}
        self.couplingAsList = []
        self.QuantumComputerCoupling = []
        self.size = 0

    def getSize(self):
        return self.size
        
    def modifyWeights(self,first,second):
     #   first = self.layout[first]
    #    second = self.layout[second]
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
        #print("Self skeleton is",self.sk)
        for i in self.sk:
            qubitFrom =self.layout[i[0]]
            qubitTo = self.layout[i[1]]
            if (t.get(qubitFrom)!= None):
                if (qubitTo not in t[qubitFrom]):
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
        self.populateDefaultLayout()

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
        minSize = 100000000000000
        myIndex = 0
        for element in smallList:
            #print("Element of paths is:",element)
            if len(element)<=minSize:
                matches = 1
                for elem in element:
                    if not self.inverseLayout.get(elem,None):
                        #print("GOTCHA:",element)
                        matches = 0
                if matches==1:
                    minSize = len(element)
                    myIndex = smallList.index(element)
                    #print("ASSIGN:",element)
                    #print("Smallist is [myindex] is:",smallList[myIndex]," its length is",len(smallList[myIndex])) 
      
        return smallList[myIndex]

    def findIndexOfTheGateSkeleton(self,notMatching):
        inn = 0
        for line in self.lines:
            tokens = line.split(" ",1)
            #todo extend the list with the others
            if tokens[0]=="t2": 
                variables=tokens[1].split()
                #print(variables,notMatching)
                if self.checkSkeletonEquivalence(variables,notMatching)==1:
                    return inn
            elif tokens[0]=="v": 
                variables=tokens[1].split()
                #print(variables,notMatching)
                if self.checkSkeletonEquivalence(variables,notMatching)==1:
                    return inn
            elif tokens[0]=="v+": 
                variables=tokens[1].split()
                #print(variables,notMatching)
                if self.checkSkeletonEquivalence(variables,notMatching)==1:
                        return inn
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
        #print("replaceTo",replaceTo)
        #print("Thing to replace",thing)
        #print("Size minus two is",size-2)
        for i in range(size-2):
            currentElem = self.inverseLayout[replaceTo[i]]
            nextElem = self.inverseLayout[replaceTo[i+1]]
            swapString = "sw "+ currentElem + " " + nextElem
            #print(swapString)
            #print("ReplaceTo is:, self.layout is:",replaceTo, self.layout)
            self.lines.insert(index+i+1,swapString)
            self.lines.insert(index+i,swapString)
        #print("Line to correct is:",self.lines[index+size-2])
        self.rebuildGate(thing,index+size-2)

    def fixTheSkeleton(self,element,replaceTo):
        skElement = str(element[0])+str(element[1])
        nskElement = str(replaceTo[0])+str(replaceTo[1])
        if self.sk.index(skElement):
            t = self.sk.index(skElement)
            self.sk[t] = nskElement
        #print("fixed skeleton",self.sk)
            
    def fixMissingEdges(self):
        for element in self.notMatching:
            #print(" The element that started this",element)
            #print("self availableShit",self.couplingAsList)
            #print("Not matching is",element," ",self.layout[element[0]],self.layout[element[1]])
            #print("Not fixed lines are",self.lines)
            #print( "Paths to",element[0],element[1])
            self.findPathWithLayout(element[0],element[1])
            
            self.getPathAndStuff()
            # Select first element record noise
            # Select second element record noise
            # Select .... elements record noise
            #print("SELF POSSIBLE PATH IS",self.possiblePath)
            self.bestPossibleEdge = self.selectLeastOccupied(self.possiblePath)
            bestPossibleEdge = self.bestPossibleEdge
            #print("Hoy",bestPossibleEdge)
            #fix the possibilities: if the first is to , then insert the swap to from and the bestPossibleEdge
            lastPair = [self.inverseLayout[bestPossibleEdge[len(bestPossibleEdge)-2]],self.inverseLayout[bestPossibleEdge[len(bestPossibleEdge)-1]]]
           # print("Last pair is:",lastPair," Element is:",element)
            replaceTo =  self.whatToReplace(element,lastPair)
            ind = self.findIndexOfTheGateSkeleton(element)
           # print("Going to update the gate at the index",ind)
            self.surroundWithSwaps(ind,bestPossibleEdge,replaceTo)
            #print("Corrected lines are:",self.lines)
            #self.fixTheSkeleton(element,replaceTo)
            #print("What to replace is:",replaceTo)
        print("Lines are:",self.lines," length of lines is:",len(self.lines))

    def transformCoupling(self,maList):
        for element in  maList:
            if (element[0] > element[1]):
                key = str(chr(element[1]+ord("a")))+str(chr(element[0]+ord("a")))
            else:
                key = str(chr(element[0]+ord("a")))+str(chr(element[1]+ord("a")))
            self.couplingAsList.append(key)
        for element in maList:
            self.coupling[chr(element[0]+ord("a"))] = set()
            self.coupling[chr(element[1]+ord("a"))] = set()
        for element in maList:
            self.coupling[chr(element[0]+ord("a"))].add(chr(element[1]+ord("a")))
            self.coupling[chr(element[1]+ord("a"))].add(chr(element[0]+ord("a")))
        return self.couplingAsList
    
    def setCoupling(self,maList):
        for element in  maList:
            key = str(chr(element[0]+ord("a")))+str(chr(element[1]+ord("a")))
            self.couplingAsList.append(key)
        return self.couplingAsList
    
    
    
    def findCurrentCost(self):
    	self.cost = 0
    	for element in self.weights:
    		self.cost = self.cost+element
        # print (self.cost)

    def findPathWithLayout(self,current,vTo):
        self.trace = []
        self.weightsForPath = []
        self.found = 0
        self.possiblePath = []
        self.cost = 0       
        vTo = self.layout[vTo]
        current = self.layout[current]
        self.findPathHelper(current,vTo,[current])

    def findPath(self,current,vTo):
        self.trace = []
        self.weightsForPath = []
        self.found = 0
        self.possiblePath = []
        self.cost = 0


        self.findPathHelper(current,vTo,[current])
        #for i in range(0,len(self.trace)-1):
        #   key = str(self.trace[i]) + str(self.trace[i+1])

    def getPathAndStuff(self):
        #print("Trace is")
        #print(self.possiblePath)
        return self.trace,self.weightsForPath

    def findHighestConnectivityNodesInCoupling(self):
        while len(self.coupling)>0:
            maximumConnections = 0
            maximumElementList = []
            for element in self.coupling:
                if len(self.coupling[element])>maximumConnections:
                    maximumElementList = []
                    maximumConnections = len(self.coupling[element])
                    maximumElementList.append((element,self.coupling[element]))
                elif len(self.coupling[element])==maximumConnections:
                    maximumConnections = len(self.coupling[element])
                    maximumElementList.append((element,self.coupling[element]))
                    
            for el in maximumElementList:
                del self.coupling[el[0]]
            self.highestConnectivityNodes.append(maximumElementList)

    def findHighestConnectivityNodesInSkeleton(self):
        qubitConnectionsCount = {}
        usedConnectionsSet = set()
        for element in self.sk:
            usedConnectionsSet.add(element)
            qubitConnectionsCount[element[0]]=qubitConnectionsCount.get(element[0],0)+1
            qubitConnectionsCount[element[1]]=qubitConnectionsCount.get(element[1],0)+1
        sortedValues = list(qubitConnectionsCount.values())
        sortedValues.sort()
        tuplesList = []
        for element in sortedValues:
            for elem in qubitConnectionsCount:
                if qubitConnectionsCount[elem] == element:
                    del qubitConnectionsCount[elem]
                    tuplesList.append((elem,element))
                    break
        #print(tuplesList)
        #self.qubitConnectionsCount = collections.OrderedDict(tuplesList)
        self.qubitConnectionsCount = list(tuplesList)

    def layOutQubits(self):
        self.recalculateWeights()
        self.findHighestConnectivityNodesInCoupling()
        self.findHighestConnectivityNodesInSkeleton()
        for element in self.highestConnectivityNodes:
            for elem in element:
                self.coupling[elem[0]]=elem[1]
        self.layout = {}
        candidates = []
        candidatesSet = set()
        placed = []
        used = set()
        #print("Initial self.qubitconnectionscount is",self.qubitConnectionsCount)
        while len (self.qubitConnectionsCount)>0:
            if len(candidates)==0:
                #print("wiggle wiggle")
               # print("Self.qubitconnectionscount is",self.qubitConnectionsCount)
                qbit = self.qubitConnectionsCount[len(self.qubitConnectionsCount)-1][0]
                while not self.layout.get(qbit[0],None):
                    if len(self.highestConnectivityNodes[0])!=0:
                        qbit = self.qubitConnectionsCount.pop()
                        physBit = self.highestConnectivityNodes[0].pop()
                    else:
                        del self.highestConnectivityNodes[0]
                        continue

                    self.layout[qbit[0]]=physBit[0]
                    #print("SELFLAYOUTOFQUBIT",qbit)
                    used.add(physBit[0])
                    placed.append((qbit[0],physBit[0]))
                    for elem in physBit[1]:
                        if not elem in used and not elem in candidatesSet:
                            candidates.append(elem)
                            candidatesSet.add(elem)
            else:
                #print("Self.qubitconnectionscount=",self.qubitConnectionsCount)
                qbit = placed[len(placed)-1][0]
                elem = placed[len(placed)-1][1]
                
                nextQbit = self.qubitConnectionsCount[len(self.qubitConnectionsCount)-1][0]
                #print("Placing together",qbit,nextQbit)
                firstPhysicalBit  = elem
                secondPhysicalBit = candidates[0]
                if  not secondPhysicalBit:
                    print("Was not able to find second physical bit")
                    raise SystemError
                self.findPath(firstPhysicalBit,secondPhysicalBit)
                minDistance = len(self.possiblePath)*len(candidates)-len(self.coupling[secondPhysicalBit])
                while not self.layout.get(nextQbit,None):
                    for secondElem in candidates:
                        #suboptimal, we can start watching at 2nd here
                        if not elem == secondElem:
                            self.findPath(elem,secondElem)
                            tempDistance =self.findPlacingDistance(placed,nextQbit,secondElem)
                            if tempDistance<minDistance and tempDistance != 0 :
                                secondPhysicalBit = secondElem
                                minDistance = tempDistance
                    self.layout[nextQbit]=secondPhysicalBit
                    candidates.remove(secondPhysicalBit)
                    used.add(secondPhysicalBit)
                    #print("Used are:",used)
                    #print("Candidates are:",candidates)
                    for elem in self.coupling[secondPhysicalBit]:
                        if not elem in used and not elem in candidatesSet:
                            candidates.append(elem)
                            candidatesSet.add(elem)
                    placed.append((nextQbit,secondPhysicalBit[0]))
                self.qubitConnectionsCount.pop()
        #print("Final layout is",self.layout)
        self.constructInverseLayout()
        #self.updateSkeletonWithLayout()
    
    def constructInverseLayout(self):
        self.inverseLayout = {}
        for elem in self.layout:
            k = elem
            v = self.layout[k]
            self.inverseLayout[v]=k

    def updateSkeletonWithLayout(self):
        for i in range(0,len(self.sk)):
            element = self.sk[i]
            lOne  = self.layout[element [0]]
            lTwo  = self.layout[element [1]]
            connection = lOne+lTwo
            if lTwo>lOne:
                connection=lTwo+lOne
            self.sk[i] = connection
        #print("NewlyUpdated skeleton is:",self.sk)

    def recalculateWeights(self):
        self.weights={}
        for elem in self.sk:
            self.weights[elem] = self.weights.get(elem,0)+1
        #print("Recalculated weights are:",self.weights)


    # We want to minimize the cost
    # this means for smallest distance 
    # we want to place the connections with biggest weight
    # minimal 
    def findPlacingDistance(self,placed,logicalQubitToPlace,physicalQubitToplace):
        cost = 0
        for element in placed:
            logicalQubitInPlaced = element[0]
            physicalQubitInPlaced = element[1]
            self.findPath(physicalQubitInPlaced,physicalQubitToplace)
            physicalLength = len(self.possiblePath)
            connection = logicalQubitInPlaced+logicalQubitToPlace
            if logicalQubitInPlaced>logicalQubitToPlace:
                connection=logicalQubitToPlace+logicalQubitInPlaced
            logicalMultiplyer = self.weights.get(connection,0)
            cost += physicalLength*logicalMultiplyer
        return cost
    
    def populateDefaultLayout(self):
        for i in range(0,self.size):
            letter = chr(ord("a")+i)
            self.layout[letter]=letter
        self.constructInverseLayout()
        
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
        self.lines = ioClass.getLines().copy()
        #print("Corrected lines are:",self.lines)
        self.resetCtg()
        for lineRead in self.lines:
            tokens = lineRead.split(" ",1)
            little_token1 = tokens[0][0]
            little_token2 = tokens[0][1]
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
            if little_token1=="t" and int(little_token2) > 3:
                controls = list()
                variables=tokens[1].split(" ")
                last = ord(variables[len(variables)-1][0])-ord('a')
                for i in range(len(variables)-1):
                    temp = ord(variables[i][0])-ord('a')
                    controls.append(temp)

                qc,qr = self.insertNControlToffoliGate(qc,qr,controls,last,ioClass.ancilaSize)
       # print (ctg.getPathAndStuff())
        return qc,qr

       
    def readFixedGatesFromCtg(self,qr,qc):
            lines = self.lines
            self.resetCtg()
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
            #print ("The updated skeleton is:",self.sk,", its length is:",len(self.sk))
            self.findHighestConnectivityNodesInSkeleton()
            #print("The most used quantum gubits are",self.qubitConnectionsCount)
            return qc,qr

    def resetCtg(self):
        self.weights = {}
        self.sk = []
        self.highestConnectivityNodes = []


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
            #self.modifyWeights(k,k2)
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

    # Assumes first second third target are lnn
    # If better realization of Toffoli gate is known, 
    # it can be updated here
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


    # TEST THOROUGHLY
    # does not require lines to be together, insert swaps
    # could be optimized by minimizing the number of swaps
    # bringing lines together
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

    def insertNControlToffoliGate(self,qc,qr,controls,target,ancilaSize):
        size_c = len(controls)
        ancila = list()
        for i in range(self.size,self.size+ancilaSize):
            ancila.append(i)
            print("Ancilla bit will have number:", i)
        size_a = len(ancila)
        print("Controls are", controls)
        print("Target is", target)
        print("Ancila after constructed is",ancila)
        qc, qr = self.insertToffoliGate(qc,qr,controls[0],controls[1],ancila[0])
        for i in range(1, size_a):
            print("DEBUG",i+2,i+1)
            qc,qr = self.insertToffoliGate(qc,qr,ancila[i],controls[i+2],ancila[i+1])
            
        qc,qr = self.insertToffoliGate(qc,qr,ancila[size_a-1],controls[size_c-1],target)
                                   
        return qc,qr
           
    def __str__(self):
        return "Weights are:"+str(self.weights)+", skeleton is:"+str(self.sk)+", vertices are"+str(self.v)+", paths are "+str(self.paths)+",latest weight are"+str(self.weightsForPath)