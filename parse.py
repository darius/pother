"""
Parse a Pother expression.
"""

import re
from crusoeparse import parse

def identity(x): return x
def ignore(*args): pass

def cons(x, xs): return [x] + xs
def singleton(x): return [x]


def make_var(v):        return v
def make_const(c):      return c
def make_lam(v, e):     return '(lambda (%s) %s)' % (v, e)
def make_app(e1, e2):   return '(%s %s)' % (e1, e2)
def make_send(e1, e2):  return '(%s <- %s)' % (e1, e2)
def make_lit_sym(v):    return '(quote %s)' % v

def make_let(decls, e):
    return '(let %s %s)' % (' '.join(decls), e)

def make_defer(v):      return '(defer %s)' % v
def make_bind(v, e):    return '(bind %s %s)' % (v, e)
def make_eqn(vs, e):    return '((%s) %s)' % (' '.join(vs), e)

def make_list_pattern(params):
    return '(list %s)' % ' '.join(map(str, params))

def make_list_expr(es):
    return '(list %s)' % ' '.join(map(str, es))

def make_case(e, cases): return ('(case %s %s)'
                                 % (e, ' '.join('(%s %s)' % pair for pair in cases)))


_ = r'\s*'
# keyword = r'(let|case|defer|bind)\b'   # no \s*
identifier = r'(?!let\b|case\b|defer\b|bind\b)([A-Za-z_]\w*)\b\s*'
operator = r'(<=|:=|[!+-.])\s*'  # XXX

string_literal = r'"([^"]*)"'

def startme(thing): return lambda: [[_,thing,                     identity]]
#print parse(startme(keyword), 'let')
#print parse(startme(identifier), 'hey')

def foldr(f, z, xs):
    for x in reversed(xs):
        z = f(x, z)
    return z

def toy_grammar(string):

    def fold_app(f, fs):  return reduce(make_app, fs, f)
    def fold_apps(fs):    return reduce(make_app, fs)
    def fold_send(f, fs): return reduce(make_send, fs, f)
    def fold_lam(vp, e):  return foldr(make_lam, e, vp)

    def start(): return [[_,E,                     identity]]

    def E():     return [[Fp,                      fold_apps],
                         [Fp, '`', V, '`', E,
                          lambda _left, _op, _right:
                              fold_app(_op, [fold_apps(_left), _right])],
                         [r'&',_,Vp,'=>',_,E,     fold_lam],   # XXX was \ for lambda
                         [r'let\b',_,Decls,E,_,    make_let],
                         [r'case\b',_,E,Cases,     make_case]]

    def Cases(): return [[Case,Cases,              cons],
                         [Case,                    singleton]]

    def Case():  return [['[|]',_,Param,'=>',_,E,  lambda _p,_e: (_p, _e)]]

    def Param(): return [[Const,                   identity],
                         [V,                       identity],
                         ['[(]',_,Param,'[)]',_,   identity],

                         [r'\[',_,ParamList,r'\]',_, identity],

#                         [Param,operator,_,Param,  
#                          lambda _left,_op,_right: [_op, _left, _right]]
                         ]

    def ParamList(): return [[Param,',',_,Param, lambda p1,p2: make_list_pattern([p1, p2])]]  # XXX hack

    def Decls(): return [[Decl,Decls,              cons],
                         [Decl,                    singleton]]
    
    def Decl():  return [[r'defer\b',_,V,';',_,          make_defer],
                         [r'bind\b',_,V,'=',_,E,';',_,   make_bind],
                         [Vp,'=',_,E,';',_,              make_eqn]]

    def Fp():    return [[F,Fs,                    cons]]
    def Fs():    return [[F,Fs,                    cons],
                         [                         lambda: []]]

    def F():     return [[Const,                   make_const],
                         [V,                       make_var],
                         ['[(]',_,E,'[)]',_,       identity],
                         ['{',_,F,_,Fp,'}',_,      fold_send],
                         [r'\[',_,EList,r'\]',_,   make_list_expr],
                         ]

    def EList(): return [[E,',',_,EList,           cons],
                         [E,                       singleton],
                         [                         lambda: []]]

    def Vp():    return [[V,Vp,                    cons],
                         [V,                       singleton]]

    def V():     return [[identifier,              identity],
                         [operator,                identity]]

    def Const(): return [['[.]',_,V,               make_lit_sym],
                         [string_literal,_,        repr],
                         [r'(-?\d+)',_,            identity],
                         ['[(]',_,'[)]',_,         lambda: '()'],
                         [r'\[',_,r'\]',_,         lambda: '[]'],
                         ]

    return parse(start, string)

print toy_grammar('let x=y; x')
print toy_grammar('')
print toy_grammar('x x . y')
print toy_grammar('(when (in the)')
print toy_grammar('&M => (&f => M (f f)) (&f => M (f f))')
print toy_grammar('&a b c => a b')

mint = r"""
let make_mint name =
    case make_brand name
      | [sealer, unsealer] =>

        let defer mint;
            real_mint name msg = case msg

              | .__print_on => &out => out .print (name .. "'s mint")

              | .make_purse => &initial_balance =>
                  (let _ = assert (is_int initial_balance);
                       _ = assert (0 .<= initial_balance);
                       balance = make_box initial_balance;
                       decr amount = (let _ = assert (is_int amount);
                                          _ = assert ((0 .<= amount) 
                                                      .and (amount .<= balance));
                                      balance .:= (balance .! .- amount));
                       purse msg = case msg
                         | .__print_on => &out =>
                             out .print ("has " .. (to_str balance)
                                                .. name .. " bucks")
                         | .balance  => balance .!
                         | .sprout   => mint .make_purse 0
                         | .get_decr => sealer .seal decr
                         | .deposit  => &amount source =>
                             (let _ = unsealer .unseal (source .get_decr) amount;
                              balance .:= (balance .! .+ amount));
                   purse);

            bind mint = real_mint;
        mint;

make_mint
"""
print toy_grammar(mint)
#print toy_grammar('let defer mint; mint')

mintskel = r"""
let make_mint name =
    case make_brand name
      | [sealer, unsealer] =>

        let defer mint;
        mint;

make_mint
"""
print toy_grammar(mintskel)

voting = r"""
let make_one_shot f =
        let armed = make_box True;
        &x => let _ = assert (armed .! .not);
                  _ = armed .:= False;
        f x;
    
    start_voting voters choices timer =
        let ballot_box = map (&_ => make_box 0) choices;
            poll voter =
                let make_checkbox pair = 
                        case pair
                          | [choice, tally] =>
                            [choice, make_one_shot (&_ => 
                                       tally .:= (tally .! .+ 1))];
                    ballot = map make_checkbox (zip choices ballot_box);
                {voter ballot};
            _ = for_each poll voters;
        [close_polls, totals];

start_voting
"""
print toy_grammar(voting)
