import llvmlite.ir as ir
module = ir.Module("test")
fnty = ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(32))])
func = ir.Function(module, fnty, name="test_vol")
builder = ir.IRBuilder(func.append_basic_block("entry"))
ptr = func.args[0]
load = builder.load(ptr)
load.volatile = True
store = builder.store(ir.Constant(ir.IntType(32), 42), ptr)
store.volatile = True

# cmpxchg testing
cmp_inst = builder.cmpxchg(ptr, ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 1), "monotonic", "monotonic")
# atomicrmw testing
xchg_inst = builder.atomic_rmw("xchg", ptr, ir.Constant(ir.IntType(32), 2), "monotonic")

print(str(module))
