'''
Created on 27/lug/2012

@author: Francesco Capozzo
'''

import myclips.parser.Types as types
from myclips.rete.tests.locations import VariableLocation, VariableReference
from myclips.MyClipsException import MyClipsBugException
import myclips

def getVar(varName, variables, inPatternVariables):
    if variables.has_key(varName):
        return variables[varName]
    
    for prevVar in inPatternVariables:
        if prevVar.name == varName:
            return prevVar
    
    return False


def analyzeSequence(sequence, variables):
    
    inPatternVariables = []
    inPatternReferences = []

    prevMultifieldCount = 0
    
    for (fIndex, field) in enumerate(sequence):
        
        field, isNegative, connectedConstraints = normalizeAtom(field)
        if len(connectedConstraints) > 0:
            myclips.logger.error("FIXME: Connected contraints ignored in sequence analysis: %s", connectedConstraints)
        
        varLocation = None
        
        if isinstance(field, (types.SingleFieldVariable, types.BaseParsedType, types.UnnamedSingleFieldVariable)):
            # ignora tutte le cose non "variabili" nell'analisi
            # ma il fatto che abbia trovato un elemento di lunghezza
            # conosciuta dopo ad un eventuale multifield
            # mi dice che il multifield nn si puo estendere oltre una
            # certa lunghezza.
            # aggiorno tutte le variabili precedenti con questa informazione
            for var in inPatternVariables:
                if var.fromEnd:
                    var.endIndex += 1

            for var in inPatternReferences:
                if var.fromEnd:
                    var.endIndex += 1
        
        if isinstance(field, types.SingleFieldVariable) and not isinstance(field, types.UnnamedSingleFieldVariable):
            # ho trovato una variabile
            # controllo se ce l'ho gia
                
            # nuova occorrenza
            varLocation = VariableLocation(field.evaluate())
            varLocation.isMultifield = False
            
            varLocation.beginIndex = fIndex
            varLocation.endIndex = 0
            
            varLocation.fromBegin = (prevMultifieldCount == 0)
            varLocation.fromEnd = (prevMultifieldCount > 0)

            
        elif isinstance(field, types.MultiFieldVariable):
            
            if not isinstance(field, types.UnnamedMultiFieldVariable):
                
                # nuova occorrenza
                varLocation = VariableLocation(field.evaluate())
                #varLocation.patternIndex = index
                varLocation.isMultiField = True
                
                varLocation.beginIndex = fIndex
                varLocation.endIndex = 0
                
                varLocation.fromBegin = (prevMultifieldCount == 0)
                varLocation.fromEnd = (prevMultifieldCount > 0)

            # DOPO AVER CREATO LA VARIABILE
            # AGGIORNO IL CONTATORE
            prevMultifieldCount += 1
            
                
        if varLocation is not None: 
            mainDefinition = getVar(varLocation.name, variables, inPatternVariables)
            if not mainDefinition:
                inPatternVariables.append(varLocation)
                
            else:
                # convert the variable location, in a variable reference
                varReference = VariableReference()
                varLocation.toVarReference(varReference)
                varReference.reference = mainDefinition
                varReference.isNegative = isNegative
                inPatternReferences.append(varReference)
    
    for var in inPatternVariables:
        if not var.fromBegin:
            var.fromBegin = None
            var.beginIndex = None
        elif not var.fromEnd:
            var.fromEnd = None
            var.endIndex = None

    for var in inPatternReferences:
        if not var.fromBegin:
            var.fromBegin = None
            var.beginIndex = None
        elif not var.fromEnd:
            var.fromEnd = None
            var.endIndex = None

    
    return (inPatternVariables, inPatternReferences)
    

def VariableAnalysis(thePatterns, variables = None, joinConstraints = None, indexPrefix = 0):
    variables = {} if variables is None else variables
    joinConstraints = [] if joinConstraints is None else joinConstraints
    for (index, thePattern) in enumerate(thePatterns):
        inPatternVariables = []
        inPatternReferences = []
        index += indexPrefix

        if isinstance(thePattern, types.AssignedPatternCE):
        
            if not not getVar(thePattern.variable.evaluate(), variables, []):
                raise MyClipsBugException("Assigned variable in assigned-pattern-CE can't be a reference")
            
            varLocation = VariableLocation()
            varLocation.name = thePattern.variable.evaluate()
            varLocation.patternIndex = index
            inPatternVariables.append(varLocation)
            
            thePattern = thePattern.pattern
        
        if isinstance(thePattern, types.OrderedPatternCE):
        
            (inPatternVariables, inPatternReferences) = analyzeSequence(thePattern.constraints, variables)
        
        if isinstance(thePattern, types.TemplatePatternCE):
            for slot in thePattern.templateSlots:
                if isinstance(slot, types.SingleFieldLhsSlot):
                    if isinstance(slot.slotValue, types.SingleFieldVariable):
                        varLocation = VariableLocation(slot.slotValue.evaluate())
                        varLocation.slotName = slot.slotName
                        varLocation.patternIndex = index
                        mainReference = getVar(slot.slotValue.evaluate(), variables, inPatternVariables)
                        if not mainReference:
                            inPatternVariables.append(varLocation)
                        else:
                            varReference = varLocation.toVarReference()
                            varReference.reference = mainReference
                            inPatternReferences.append(varReference)
                            
                else:
                    (inPatternVariables, inPatternReferences) = analyzeSequence(slot.slotValue, variables)
                    for var in inPatternVariables:
                        var.patternIndex = index
                        var.slot = slot.slotName
                    for var in inPatternReferences:
                        var.patternIndex = index
                        var.slot = slot.slotName
                
        # set patternIndex to variables and references
        for var in inPatternVariables:
            var.patternIndex = index

        for var in inPatternReferences:
            var.relPatternIndex = var.reference.patternIndex - index
                    
        variables.update(dict([(var.name, var) for var in inPatternVariables]))
        joinConstraints.append(inPatternReferences)
        
    return (variables, joinConstraints)

def normalizeAtom(atom):
    
    isNegative = False
    connected = []
    while not isinstance(atom, (types.Variable, types.BaseParsedType, types.FunctionCall)):
        if isinstance(atom, types.ConnectedConstraint):
            atom = atom.constraint
            connected = atom.connectedConstraints
        
        elif isinstance(atom, types.Constraint):
            atom = atom.constraint
            
        elif isinstance(atom, types.PositiveTerm):
            atom = atom.term
            
        elif isinstance(atom, types.NegativeTerm):
            atom = atom.term
            isNegative = True
    
    return (atom, isNegative, connected)

def analyzePattern(thePattern, patternIndex, variables):
    inPatternReferences = []
    inPatternVariables = []

    if isinstance(thePattern, types.OrderedPatternCE):
    
        (inPatternVariables, inPatternReferences) = analyzeSequence(thePattern.constraints, variables)
    
    if isinstance(thePattern, types.TemplatePatternCE):
        for slot in thePattern.templateSlots:
            if isinstance(slot, types.SingleFieldLhsSlot):
                
                # normalize to basetype or variable
                slotValue, isNegative, connectedConstraints = normalizeAtom(slot.slotValue)
                if len(connectedConstraints) > 0:
                    myclips.logger.error("FIXME: Connected contraints ignored in pattern analysis: %s", connectedConstraints)
                
                if isinstance(slotValue, types.SingleFieldVariable):
                    varLocation = VariableLocation(slotValue.evaluate())
                    varLocation.slotName = slot.slotName
                    varLocation.fullSlot = True
                    mainReference = getVar(slotValue.evaluate(), variables, inPatternVariables)
                    if not mainReference:
                        inPatternVariables.append(varLocation)
                    else:
                        varReference = VariableReference()
                        varLocation.toVarReference(varReference)
                        varReference.reference = mainReference
                        varReference.isNegative = isNegative
                        inPatternReferences.append(varReference)
                        
            else:
                (inPatternVariables, inPatternReferences) = analyzeSequence(slot.slotValue, variables)
                for var in inPatternVariables:
                    var.slot = slot.slotName
                for var in inPatternReferences:
                    var.slot = slot.slotName

    for var in inPatternVariables:
        var.patternIndex = patternIndex

    for var in inPatternReferences:
        var.relPatternIndex = var.reference.patternIndex - patternIndex

    return (inPatternVariables, inPatternReferences)
