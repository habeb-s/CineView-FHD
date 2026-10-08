import marshal, sys, types
co = marshal.loads(open(sys.argv[1], "rb").read()[16:])
def walk(c):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == "status_text":
                return [x for x in k.co_consts if isinstance(x, str) and "CineView MLA" in x]
            r = walk(k)
            if r: return r
print(sys.argv[2], walk(co))
