import re
TOK=re.compile(r'"(?:[^"\\]|\\.)*"|[{}\[\]:,]|[^\s{}\[\]:,]+',re.S)
def lex(s):
    return [t for t in TOK.findall(s)]
class P:
    def __init__(s,t): s.t=t; s.i=0
    def peek(s): return s.t[s.i] if s.i<len(s.t) else None
    def next(s): v=s.t[s.i]; s.i+=1; return v
    def val(s):
        c=s.peek()
        if c=='{': return s.obj()
        if c=='[': return s.arr()
        return s.scalar(s.next())
    def scalar(s,v):
        if v.startswith('"'): return ('s',v[1:-1])
        if v in ('true','false'): return ('b',v=='true')
        m=re.fullmatch(r'(-?[\d.]+)([bslfdLBSLFD]?)',v)
        if m: return ('n',float(m.group(1)))
        return ('s',v)
    def obj(s):
        s.next(); d={}
        while s.peek()!='}':
            if s.peek()==',': s.next(); continue
            k=s.next().strip('"'); assert s.next()==':' , k
            d[k]=s.val()
        s.next(); return d
    def arr(s):
        s.next(); a=[]
        while s.peek()!=']':
            if s.peek()==',': s.next(); continue
            a.append(s.val())
        s.next(); return a
def parse(path): return P(lex(open(path,encoding='utf-8').read())).val()
