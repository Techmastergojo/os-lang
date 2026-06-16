import llvmlite.ir as ir
module = ir.Module("test")
fnty = ir.FunctionType(ir.VoidType(), [])
func = ir.Function(module, fnty, name="my_naked_func")
func.attributes.add("naked")
print(str(func))
