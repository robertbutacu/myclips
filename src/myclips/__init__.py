
from myclips.rete.Network import Network
from myclips.parser.Parser import Parser
import myclips.parser.Types as types

import logging as _logging

VERSION="0.0-dev"

FORMAT = '[%(levelname).3s %(module)s::%(funcName)s:%(lineno)d] %(message)s'
_logging.basicConfig(format=FORMAT)

logger = _logging.getLogger('myclips')
logger.setLevel(_logging.ERROR)

# THIS FLAG WILL BE USEFULL IF
# A STRICT_MODE WILL BE AVAILABLE 
STRICT_MODE=False

def newInstance_fromCanonicalClassname(qclass, constrParams=None):
    
    if constrParams == None:
        constrParams = []
    
    lastdot = qclass.rfind('.')
    modulename = qclass[0:lastdot]
    classname = qclass[lastdot + 1:]
    
    return newInstance(classname, constrParams, modulename)
    
    #__import__('icse.ps.constraints.OrChain')
    #chain2 = globals()['OrChain']()
    
def newInstance(classname, constrParams=None, modulename=None):
    
    if constrParams == None:
        constrParams = []
    
    
    if modulename != None:
        imported = __import__(modulename, globals(), locals(), [classname], -1)
        attr = getattr(imported, classname)
        #print "creo: "+classname+" con ",constrParams
        if isinstance(constrParams, list):
            return attr(*constrParams)
        elif isinstance(constrParams, dict):
            return attr(**constrParams)
        else:
            return attr()
    else:
        if isinstance(constrParams, list):
            return globals()[classname](*constrParams)
        elif isinstance(constrParams, dict):
            return globals()[classname](**constrParams)
        else:
            return globals()[classname]()

def importPath(fullpath):
    '''
    Importa un modulo da qualsiasi percorso (fullpath) deve essere
    un percorso assoluto. Con percorsi relativi gli effetti
    potrebbero essere "interessanti" :)
    Una volta caricato il modulo, la path viene rimossa dalla sourcepath
    '''
    import sys
    import os
    path, filename = os.path.split(fullpath)
    filename, _ = os.path.splitext(filename)
    sys.path.insert(0, path)
    module = __import__(filename)
    reload(module) # Might be out of date
    del sys.path[0]
    return module


def main():
    t = """
    
    (deffunction FunzioneTest (?a)
        (printout t "Funzione di test: " ?a crlf)
        (if (integerp ?a) then
            (bind ?return (+ ?a 1))
        else
            (bind ?return -10))
        (facts)
        (retract *)
        (facts)
        ?return
    )
    
    (deffunction Test2 (?vector)
        (if (= (length$ ?vector) 2) then
            (bind ?theValue (nth$ 2 ?vector))
        else
            (bind ?theValue (nth$ 1 (first$ ?vector))))
        ?theValue
    )
    
    (deffunction Domanda (?testo ?spiegazione $?valori_ammessi)
        (format t ?testo)
        (if (neq ?spiegazione "") 
            then (format t " (%s perche) " (implode$ $?valori_ammessi))
            else (format t " (%s)" (implode$ $?valori_ammessi)))
        (format t "? ")
        (bind ?risposta (read))
        (if (lexemep ?risposta)                              
            then (bind ?risposta (lowcase ?risposta)))       
        (if (eq ?risposta perche)
            then (format t (str-cat "%n" ?spiegazione "%n") ))
        (while (not (member$ ?risposta $?valori_ammessi)) do
            (format t ?testo)
            (if (neq ?spiegazione "") 
                then (format t "(%s perche)" (implode$ $?valori_ammessi))
                else (format t "(%s)" (implode$ $?valori_ammessi)))
        (format t "? ")
        (bind ?risposta (read))
        (if (lexemep ?risposta)
            then (bind ?risposta (lowcase ?risposta))))
        ?risposta
    )
    
            
    
    (deftemplate A 
        (slot a)
        (slot b))
        
    (deffacts df 
        (A B C D)
        (A (a 1) (b 2)))
        
    (defrule r 
        (A B C D) 
        => 
        (printout t "blablabl" crlf)
        (assert (D C B A))
    )
    (defrule r2
        ?f <- (D C B A)
        =>
        (printout t "Trovato: " ?f crlf)
        (loop-for-count (?cnt1 2 4) do
            (loop-for-count (?cnt2 1 3) do
                (loop-for-count 2 do
                    (printout t ?cnt1 " " ?cnt2 crlf))))
    )
    (defrule r3
        ?f <- (A (a 1) (b 2))
        =>
        (printout t "Modify: " (modify ?f (a 3) (b 10)) crlf)
    )
    (defrule r4
        ?f <- (A (a 3) (b 10))
        =>
        (printout t "MODIFICA OK" crlf)
        (printout t "Duplicate: " (duplicate ?f (b 1000)) crlf)
        (printout t "Assert-string: " (assert-string "(A Z E D)") crlf)
        (printout t "Fact-Index: " (fact-index ?f) crlf)
        (printout t "Risultato: " (+ 1 (FunzioneTest 10)) crlf)
        (printout t "Risultato: " (+ 1 (FunzioneTest "ciao")) crlf)
        (printout t "Altra funzione: " (Test2 (create$ 1 2)) crlf)
        (printout t "Altra funzione: " (Test2 (create$ 1 2 3)) crlf)
        (Domanda "Il paziente ha febbre?" "" si no)
    )
    """
    n = Network()
    try:
        parsed = n.getParser().parse(t, True)
    except Exception, e:
        print n.getParser().ExceptionPPrint(e, t)
    else:
        n.addDeffacts(parsed[0])
        n.addRule(parsed[1])
        n.addRule(parsed[2])
        n.addRule(parsed[3])
        n.addRule(parsed[4])
        print n.facts
        print n.reset()
        print n.facts
        for (salience, pnode, token) in n.agenda.activations():
            print "%-6d %s: %s"%(salience, pnode.mainRuleName, token)
    
        return n

