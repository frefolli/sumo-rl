set -e

function process_file() {
  BASE=$1
  FILE=$2
  CONF=$3
  rm -rf outputs/$FILE
  rm -rf outputs/$BASE
  python -m main -s $BASE $CONF
  python -m sumo_rl.util.plot -s $BASE
  mv outputs/$BASE outputs/$FILE
}

PRJ=fiore
process_file $PRJ $PRJ-mono-fixed "-A fixed -O default -R dwt -P mono  -r"
process_file $PRJ $PRJ-mono-ql    "-A ql    -O default -R dwt -P mono  -r"
process_file $PRJ $PRJ-size-ql    "-A ql    -O default -R dwt -P size  -r"
process_file $PRJ $PRJ-space-ql   "-A ql    -O default -R dwt -P space -r"
