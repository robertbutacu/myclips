'''
Created on 30/lug/2012

@author: Francesco Capozzo
'''
from myclips.rete.Node import Node
from myclips.rete.BetaInput import BetaInput
from myclips.rete.Memory import Memory
import myclips.parser.Types as types
from myclips.rete.Token import Token
from myclips.rete.tests.locations import VariableLocation
from myclips.functions import FunctionEnv
#from myclips.FunctionsManager import FunctionDefinition
from myclips.functions.Function import Function

class PNode(Node, BetaInput, Memory):
    '''
    classdocs
    '''


    def __init__(self, ruleName, leftParent, network, orClauseCount=None, rhs=None, properties=None, moduleName=None, variables=None):
        '''
        Constructor
        '''
        self._ruleName = ruleName + (("~"+str(orClauseCount)) if orClauseCount is not None else "")
        self._isMain = (orClauseCount is None)
        self._network = network
        self._rhs = rhs
        self._linkedPNodes = []
        self._properties = {"salience": 0, "auto-focus": False} if properties is None or not isinstance(properties, dict) else properties
        self._moduleName = moduleName if moduleName is not None else network.modulesManager.currentScope.moduleName
        self._variables = variables if isinstance(variables, dict) else {}

        Node.__init__(self, leftParent=leftParent)
        Memory.__init__(self)


    def leftActivation(self, token, wme):
        #myclips.logger.debug("FIXME: PNode left activation NIY. token=%s, wme=%s", token, wme)
        newToken = Token(self, token, wme)
        self.addItem(newToken)
        self._network.agenda.insert(self, newToken)
        
    def removeItem(self, item):
        # remove the item from the memory
        Memory.removeItem(self, item)
        # and remove the activation
        self._network.agenda.remove(self, item)
        
    def delete(self, notifierRemoval=None, notifierUnlinking=None):
        if self.isMain:
            for linkedNode in self._linkedPNodes:
                linkedNode.delete(notifierRemoval, notifierUnlinking)
                
            self._linkedPNodes = []
            
        Memory.delete(self)
        Node.delete(self, notifierRemoval, notifierUnlinking)

    def linkOrClause(self, pnode):
        self._linkedPNodes.append(pnode)
        
    def getLinkedPNodes(self):
        return self._linkedPNodes

    @property
    def isMain(self):
        return self._isMain
    
    @property
    def ruleName(self):
        return self._ruleName
    
    @property
    def mainRuleName(self):
        return self.ruleName.rsplit("~", 2)[0]
    
    @property
    def moduleName(self):
        return self._moduleName
    
    def completeMainRuleName(self):
        return self.moduleName+"::"+self.mainRuleName
    
    def completeRuleName(self):
        return self.moduleName+"::"+self.ruleName
    
    def __hash__(self):
        return hash(self.completeRuleName())
    
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.ruleName == other.ruleName and
                self.isMain == other.isMain and
                self.completeRuleName() == other.completeRuleName() and
                self.getSalience() == other.getSalience() and
                self.isAutoFocus() == other.isAutoFocus() and
                self.leftParent == other.leftParent and
                self.rhs == other.rhs)
        
    def __neq__(self, other):
        return not self.__eq__(other)
    
    def getSalience(self):
        return int(self.getProperty("salience", 0))
    
    def isAutoFocus(self):
        return bool(self.getProperty("auto-focus", False))
    
    def getProperty(self, propName, defaultValue):
        return self._properties.get(propName, defaultValue)
    
    def __str__(self, *args, **kwargs):
        return "<{0}: name={2}, left={3}, items={4}>".format(
                        self.__class__.__name__,
                        str(id(self)),
                        self.ruleName,
                        str(id(self.leftParent)) if not self.isLeftRoot() else "None",
                        len(self._items)
                    )
    
    # FIXME move following methods into a AgendaActivation Class
    
    def execute(self, theToken):
        
        # resolve variables from the token
        resolved = {}

        linearToken = theToken.linearize()
        
        for theVar, theLocation in self._variables.items():
            try:
                assert isinstance(theLocation, VariableLocation)
                resolved[theVar] = theLocation.toValue(linearToken[theLocation.patternIndex])
            except:
                import myclips
                myclips.logger.debug("%s: unresolvable variable %s: %s:%s %s", self.completeRuleName(), theVar, theLocation.patternIndex, theLocation, linearToken )
        
        # prepare the FunctionEnv object    
        theEnv = FunctionEnv(resolved, self._network, self._network.modulesManager, self._network.resources)
        
        # execute all rhs passing FunctionEnv
        # theEnv could be modified from the function call.
        # This THE way to share memory between functions
        
        for action in self._rhs:
            assert isinstance(action, types.FunctionCall)
            
            # get the function definition linked to the FunctionCall
            #funcDefinition = action.funcDefinition
            
            #assert isinstance(funcDefinition, FunctionDefinition)
            # expand the args 
            #funcDefinition.linkedType.__class__.execute(funcDefinition.linkedType, theEnv, *(action.funcArgs))
            
            Function.doExecute(action, theEnv)
        
        # ...
        
        # profit?!
        
    
    
    