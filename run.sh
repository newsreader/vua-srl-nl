#!/usr/bin/bash

# This script runs the Dutch SRL pipeline together
# it takes a NAF file with terms and Alpino dependencies as input
# and runs the data through timbl
# for more info, see the README
#  
# author: Marieke van Erp 
# date: 27 September 2014 

inputfile=$1
outputfile=${inputfile%.naf}.sonarsrl.naf

# First step is to create a feature vector from the NAF file
cat $inputfile | python nafAlpinoToSRLFeatures.py > timblfile.csv

# Run the trained model on the newly created feature vector  
# To do: also build a timbl server option
timbl -mO:I1,2,3,4 -i e-mags_mags_press_newspapers.wgt -t timblfile.csv -o timblpredictions 

# Insert the SRL values into the NAF file 
python timblToAlpinoNAF.py $inputfile timblpredictions > $outputfile
 


