#!/bin/bash
#SBATCH --account=f.refolli-thesis             # Account
#SBATCH --job-name=sumo-rl                     # Job name
# RESOURCES
#SBATCH --ntasks=1                             # How many tasks
#SBATCH --cpus-per-task=2                      # How many MPI cores per task
#SBATCH --mem=2G                               # Job memory request
#SBATCH --time=01:30:00                        # Time limit hrs:min:sec
# OUTPUT FILES
#SBATCH --output=job_logs/out_%x_%j.log        # Standard output and error log, with job name and id
# NOTIFICATION EMAILS
#SBATCH --mail-type=ALL                        # Valid types are: NONE, BEGIN, END, FAIL, ALL
#SBATCH --mail-user=f.refolli@campus.unimib.it # User to receive email notifications

### Definitions
export BASEDIR="Projects/sumo-rl"

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
tar cvf 4.tar experiments/4

### File system cleanup

### Footer
date    #prints last line of output file
