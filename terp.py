from clutch import Clutch, Box
from env import Env, EmptyEnv


def run(expr, env):
    state = start(expr, env)
    while state.is_runnable():
        state = state.step()
    return state.get_value()

def start(expr, env):
    return expr.eval(env, FinalK())


# States

def RunningState(value, k):
    def to_is_runnable(): return True
    def to_step():        return k.step(value)
    def to_trace():       return repr((value, k))
    def to___repr__():    return repr((value, k))
    return Clutch(locals())

def StoppedState(value):
    def to_is_runnable(): return False
    def to_step():        assert False, 'Stopped process stepped'
    def to_trace():       return '<stopped>'
    def to___repr__():    return '<stopped>'
    def to_get_value():   return value
    return Clutch(locals())


# Continuations

class Cont(Clutch):
    def __str__(self):
        return '\n'.join(reversed(self.get_backtrace()))
    def __repr__(self):
        return '|'.join(self.get_backtrace())
    def get_backtrace(self):
        return [k.show_frame() for k in ancestry(self)]
        
def ancestry(k):
    while True:
        yield k
        k = k.get_parent()
        if k is None:
            break

def FinalK():
    def to_step(value):
        return StoppedState(value)
    def to_show_frame():
        return '<stop>'
    def to_get_parent():
        return None
    return Cont(locals())


# AST types

def ConstantExpr(value):
    def to_eval(env, k):
        return RunningState(value, k)
    def to___repr__():
        return "'" + repr(value)
    return Clutch(locals())

def VarRefExpr(variable):
    def to_eval(env, k):
        return RunningState(env.get(variable), k)
    def to___repr__():
        return repr(variable)
    return Clutch(locals())

def LambdaExpr(variable, expr):
    def to_eval(env, k):
        return RunningState(Procedure(env, variable, expr), k)
    def to___repr__():
        return '(lambda %s %r)' % (variable, expr)
    def to_make_closure(env):
        return Procedure(env, variable, expr)
    return LambdaExprClass(locals())

class LambdaExprClass(Clutch): pass

def Procedure(env, variable, expr):
    def to_call(arg, k):
        return expr.eval(Env(variable, arg, env), k)
    def to___repr__():
        return '#<procedure>'
    return Clutch(locals())

def CallExpr(rator, rand):
    def to_eval(env, k):
        return rator.eval(env, EvRandK(rand, env, k, rator))
    def to___repr__():
        return '(%r %r)' % (rator, rand)
    return Clutch(locals())

def EvRandK(rand, env, k, rator):
    def to_step(fn):
        return rand.eval(env, CallK(fn, env, k, rator, rand))
    def to_show_frame():
        return '(<%r> %r)' % (rator, rand)
    def to_get_parent():
        return k
    return Cont(locals())

def CallK(fn, env, k, rator, prev_rands):
    def to_step(arg):
        return fn.call(arg, k)
    def to_show_frame():
        return '(<%r %r>)' % (rator, rand)
    def to_get_parent():
        return k
    return Cont(locals())


# Smoke test

one = ConstantExpr(1)
f = LambdaExpr('x', VarRefExpr('x'))
test1 = CallExpr(f, one)

print run(test1, EmptyEnv())
