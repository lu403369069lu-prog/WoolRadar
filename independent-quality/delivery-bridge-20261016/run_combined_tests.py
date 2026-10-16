"""Run root and bridge formal tests in one suite without module-name collisions."""
import importlib.util,sys,unittest
from pathlib import Path
bridge=Path(__file__).resolve().parent
root=bridge.parents[1]
sys.path[:0]=[str(root),str(bridge)]
suite=unittest.TestLoader().discover(str(root/'tests'))
for path in sorted(bridge.glob('test_*.py')):
    name='wool_delivery_'+path.stem
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    suite.addTests(unittest.TestLoader().loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
