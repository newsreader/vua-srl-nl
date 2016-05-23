#!/bin/bash

# This script runs the Dutch SRL pipeline together
# it takes a NAF file with terms and Alpino dependencies as input
# and runs the data through timbl
# for more info, see the README
#  
# author: Marieke van Erp 
# date: 27 September 2014 
# Update: 25 February 2015: new model 

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# [WvA] Create temp file for input and intermediate files
TMPFIL=`mktemp -t stap6.XXXXXX`
cat >$TMPFIL

TMPFILOUT=`mktemp -t stap6.XXXXXX`
TMPFILCSV=`mktemp -t stap6.XXXXXX`

# First step is to create a feature vector from the NAF file
python $DIR/nafAlpinoToSRLFeatures.py  < $TMPFIL  > $TMPFILCSV

timbl -mO:I1,2,3,4 -i $DIR/25Feb2015_e-mags_mags_press_newspapers.wgt -t $TMPFILCSV -o $TMPFILOUT +vs >&2;

# Insert the SRL values into the NAF file 
python $DIR/timblToAlpinoNAF.py $TMPFIL $TMPFILOUT

rm $TMPFIL
rm $TMPFILOUT
rm $TMPFILCSV
