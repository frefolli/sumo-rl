set -e

function dostuff() {
  TYPE=$1
  mv outputs-$TYPE outputs
  python -m tools.plot
  mv outputs outputs-$TYPE
}

dostuff dqn
dostuff ql
dostuff fixed
