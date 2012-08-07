'''
Created on 07/aug/2012

@author: Francesco Capozzo
'''
from myclips.FunctionsManager import FunctionDefinition, Constraint_ArgType,\
    Constraint_ExactArgsLength
import myclips.parser.Types as types
from myclips.functions.Function import Function, InvalidArgTypeError


class Upcase(Function):
    '''
    The upcase function will return a string or symbol with uppercase alphabetic characters.
       
    @see: http://www.comp.rgu.ac.uk/staff/smc/teaching/clips/vol1/vol1-12.3.html#Heading237
    '''
    def __init__(self, *args, **kwargs):
        Function.__init__(self, *args, **kwargs)
        
        
    def do(self, theEnv, theString, *args, **kargs):
        """
        handler of the function
        @see: http://www.comp.rgu.ac.uk/staff/smc/teaching/clips/vol1/vol1-12.3.html#Heading237
        """
        
        # normalize theString
        if isinstance(theString, (types.Variable, types.FunctionCall)):
            theString = self.resolve(theEnv, theString)
        if isinstance(theString, types.String):
            theContent = theString.evaluate()[1:-1]
        elif isinstance(theString, types.Symbol):
            theContent = theString.evaluate()
        else:
            raise InvalidArgTypeError("Function upcase expected argument #1 to be of type string or symbol")
        
        return theString.__class__(theContent.upper())
        
        
    
Upcase.DEFINITION = FunctionDefinition("?SYSTEM?", "build", Upcase(), (types.String, types.Symbol, types.Lexeme), Upcase.do,
            [
                Constraint_ExactArgsLength(1),
                Constraint_ArgType((types.String, types.Symbol, types.Lexeme), 0),
            ],forward=False)
        
        