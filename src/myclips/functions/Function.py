'''
Created on 31/lug/2012

@author: Francesco Capozzo
'''
from myclips.MyClipsException import MyClipsException
import myclips.parser.Types as types
import traceback

        
class Function(object):
    '''
    Base abstract class for system function definition
    '''
    
    # @type DEFINITION: myclips.FunctionsManager.FunctionDefinition.FunctionDefinition
    DEFINITION = None
    
    def __init__(self, *args, **kwargs):
        object.__init__(self, *args, **kwargs)
        
    @staticmethod
    def doExecute(theFunction, theEnv, triggerEvent=True):
        from myclips.EventsManager import EventsManager
        try:
            theEnv.network.eventsManager.fire(EventsManager.E_ACTION_PERFORMED, theFunction.funcDefinition.name, theFunction.funcArgs )
        except:
            pass
        returnValue = theFunction.funcDefinition.linkedType.__class__.execute(theFunction.funcDefinition.linkedType, theEnv, *(theFunction.funcArgs))
        try:
            theEnv.network.eventsManager.fire(EventsManager.E_ACTION_RETURNVALUE, returnValue )
        except:
            pass
        return returnValue

    @classmethod
    def execute(cls, theFunction, theEnv, *args, **kargs):
        """
        Execute a function handler with correct parameters
        
        @raise FunctionImplError: forward exception from function handler implementation
        @raise FunctionInternalError: wrap a non FunctionImplError exception in a FunctionInternalError
                to hide function internal processing. Original exception is available in 
                FunctionInternalError.args[1]. Original exception repr() is used as
                wrapper exception's message
        @return: forward handler return
        @rtype: mixed (based on FunctionDefinition.returnTypes)
        """
        try:
            # this calling protocol is valid for system function
            # user function have to override this protocol
            # to use theFunction call instead
            return cls.DEFINITION.handler(cls.DEFINITION.linkedType, theEnv, *args, **kargs)
        #except ReturnException, e:
            # convert a returnException to a return value of the function
            #return e.returnValue
        except (ReturnException, BreakException, HaltException):
            # break the execution until a catch get it
            raise
        except FunctionImplError:
            raise
        except MyClipsException, e:
            raise FunctionInternalError(e.message, e, traceback.format_exc())
        except Exception, e:
            # wrap python standards exception
            # in functions exception
            raise FunctionInternalError(str(e), e, traceback.format_exc())
        
    def definition(self):
        """
        Get the system function FunctionDefinition
        """
        return self.__class__.DEFINITION
    
    def resolve(self, theEnv, arg):
        """
        Resolve the python value of a BaseParsedType
        or a a BaseParsedType for FunctionCall and Variables
        
        This function could be used in conjuction with the simplify
        to alway return a python value from an arg
        """
        # String is a special value, have to trim out quotes
        if isinstance(arg, types.String):
            return arg.content[1:-1]
        elif isinstance(arg, types.BaseParsedType):
            return arg.evaluate()
        elif isinstance(arg, types.FunctionCall):
            # indirect recursion on execute with
            #return arg.funcDefinition.linkedType.__class__.execute(arg.funcDefinition.linkedType, theEnv, *(arg.funcArgs))
            return Function.doExecute(arg, theEnv)
        elif isinstance(arg, (types.SingleFieldVariable, types.MultiFieldVariable )):
            # resolve the variable value vs theEnv.variables dict
            return theEnv.variables[arg.evaluate()]
        elif isinstance(arg, types.GlobalVariable):
            # resolve the variable value vs theEnv.globals
            return theEnv.modulesManager.currentScope.globalsvars.getDefinition(arg.evaluate()).linkedType.runningValue
        elif isinstance(arg, (list, tuple)):
            # recursiong to resolve for inner objects
            return [self.resolve(theEnv, x) for x in arg]
        else:
            return arg
        
    def simplify(self, theEnv, arg, checkType=None, errorFormat=None):
        '''
        Execute a simplification of the arg if the arg
        is a function or a variable and return the BaseParsedType
        result of the simplification
        
        Optionally, it could execute some type check and return
        an error in the format of
            "Function %cls.DEFINITION.name expected argument #%str(errorFormat[0]) to be of type %str(errorFormat[1])"
        if errorFormat is a tuple with at least 2 string elements, otherwise the error format is
            "Expected EXPECTED_TYPE, found FOUND_TYPE"
            
        @param theEnv: the system environment for the function execution
        @type theEnv: FunctionEnv
        @param arg: the arg to simplify
        @type arg: BaseParsedType|FunctionCall|Variable
        @param checkType: a type or a tuple of types to check the
            simplified arg type against to
        @type checkType: ParsedType|tuple|None
        @param errorFormat: a tuple with error parameters or None
        @type errorFormat: tuple
        @return: the simplified value if type constraints are ok (if any)
        @rtype: BaseParsedType
        @raise InvalidArgTypeError: if simplified value is not of the expected type(s)
        '''
        if isinstance(arg, (types.FunctionCall, types.Variable)):
            theResolved = self.resolve(theEnv, arg)
        elif isinstance(arg, (list, tuple)):
            theResolved = [self.semplify(theEnv, x) for x in arg]
        else:
            theResolved = arg
            
        if checkType is not None:
            if not isinstance(theResolved, checkType):
                try:
                    raise InvalidArgTypeError("Function %s expected argument #%s to be of type %s"%(self.DEFINITION.name, errorFormat[0], errorFormat[1]) )
                except (AttributeError, IndexError, KeyError):
                    raise InvalidArgTypeError("Expected %s, found %s"%(str(checkType), theResolved.__class__.__name__))
                
        return theResolved
    
    #: Alias
    semplify = simplify

class FunctionImplError(MyClipsException):
    """
    The base error class for exception raised
    inside function implementation code
    """
    pass

class HaltException(MyClipsException):
    """
    Used by Halt function to stop
    all activation execution
    """
    pass

class ReturnException(MyClipsException):
    """
    Exception used by the Return function
    to return a value from an inner function/loop
    stopping function execution flow
    """
    def __init__(self, returnValue=None, message="", *args, **kwargs):
        MyClipsException.__init__(self, message=message, *args, **kwargs)
        self.returnValue = returnValue

class BreakException(MyClipsException):
    """
    Break a loop execution flow and return
    control to a parent function
    """
    pass

class InvalidArgValueError(FunctionImplError):
    """
    An invalid value for a function argument
    """
    pass

class InvalidArgTypeError(FunctionImplError):
    """
    An invalid type for a function argment
    """
    pass

class InvalidArgsNumberError(FunctionImplError):
    """
    The number of args for a function is invalid
    """
    pass

class FunctionInternalError(FunctionImplError):
    """
    A generic, implementation based exception
    (usually to wrap python-based exception)
    """
    pass

