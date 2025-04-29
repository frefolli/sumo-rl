#!/bin/bash
#SBATCH --account=f.refolli-thesis             # Account
#SBATCH --job-name=sumo-rl                     # Job name
# RESOURCES
#SBATCH --ntasks=1                             # How many tasks
#SBATCH --cpus-per-task=2                      # How many MPI cores per task
#SBATCH --mem=2G                               # Job memory request
#SBATCH --time=07:00:00                        # Time limit hrs:min:sec
# OUTPUT FILES
#SBATCH --output=job_logs/out_%x_%j.log        # Standard output and error log, with job name and id
# NOTIFICATION EMAILS
#SBATCH --mail-type=ALL                        # Valid types are: NONE, BEGIN, END, FAIL, ALL
#SBATCH --mail-user=f.refolli@campus.unimib.it # User to receive email notifications

### Definitions
export BASEDIR="Projects/sumo-rl"
export EXP_NUM=2
set -e # CRASH IF SOMETHING CRASHES

### File System Setup
cd $HOME/$BASEDIR                  # use a folder in home directory

### Header
pwd; hostname; date    #prints first line of output file

### Software dependencies
# unloads every module
module purge
# load dependencies
module load sw/amd/gcc-8.5.0/python-3.13.3
module load sw/amd/gcc-8.5.0/sumo-1.22.0

### Executable script
#
. ./env/bin/activate
. .env
python -m tools.executor

rm -rf experiments/$EXP_NUM/rounds.tar.zst
rm -rf experiments/$EXP_NUM/archive.tar.zst

cd experiments/$EXP_NUM
cp -r ../../archive archive
tar cvf archive.tar archive && zstd archive.tar && rm archive.tar
tar cvf rounds.tar rounds && zstd rounds.tar && rm rounds.tar
rm ./archive -rf
cd $HOME/$BASEDIR
tar cvf $EXP_NUM.tar experiments/$EXP_NUM && zstd $EXP_NUM.tar && rm $EXP_NUM.tar

git add experiments/$EXP_NUM/rounds.tar.zst
git add experiments/$EXP_NUM/archive.tar.zst
git commit -m "Autocommit for JOB of Experiment $EXP_NUM!"
git push

### File system cleanup

### Footer
date    #prints last line of output file
