#!/bin/bash
# Helper script to run other extraction tasks
# Input argument is output format for image files (png or jpg)

if [ "$#" -ne 1 ]; then
	echo "This script takes 1 parameter, the path to the data directory, e.g.,"
	echo "./scripts/extractAll.sh ./sampleData" 
	echo "Optionally you can also specify the image format:"
	echo "./scripts/extractAll.sh ./sampleData png" 
fi

# Format for extracted images.
# Use png for best quality.
fmt=${2-jpg}

# Figure out the path of helper scripts
DIR=$(dirname $(readlink -f $0))
OLDDIR=$PWD

cd $1

# Extract skeletons
if [ -f vgaPose3d_stage1.tar ]; then
	tar -xf vgaPose3d_stage1.tar
fi

if [ -f hdPose3d_stage1.tar ]; then
	tar -xf hdPose3d_stage1.tar
fi



# Extract VGA images
$DIR/vgaImgsExtractor.sh ${fmt}

# Extract HD images
$DIR/hdImgsExtractor.sh ${fmt}

cd $OLDDIR
