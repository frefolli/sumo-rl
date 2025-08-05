from tools.executor.executor import Executor
import sys

if __name__ == '__main__':
  executor = Executor()
  executor.apply(sys.argv[1:])
