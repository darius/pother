from clutch import Clutch

class EnvClass(Clutch):
    def __repr__(self):
        return '#<environment>'

def EmptyEnv():
    def to_get(var):
         # XXX what type of exception should this be?
        raise Exception('Unbound variable', var)
    return EnvClass(locals())

# XXX simplify since we only have one var/val pair

def OuterEnv(frame):
    return _make_env(dict(frame), EmptyEnv())

def Env(var, val, enclosing):
    return _make_env({var: val}, enclosing)

def _make_env(frame, enclosing):
    assert isinstance(enclosing, EnvClass), \
        'Enclosing environment not an environment: %r' % enclosing
    def to_get(var):
        return frame[var] if var in frame else enclosing.get(var)
    return EnvClass(locals())
