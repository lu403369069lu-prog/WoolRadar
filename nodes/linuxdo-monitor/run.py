from pathlib import Path
import sys
ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
from nodes.run_node import main
raise SystemExit(main('linuxdo-monitor'))
