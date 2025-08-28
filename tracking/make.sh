#!/bin/bash

set -xe

tmp_file="temp_tracking.sad"

# Create the temporary script with the modified action
#for action in 0.7  0.8  0.9  1.0  1.1  1.2  1.3  1.4  1.5  1.6  1.7  1.8  1.9  2.0
for action in 2.2 2.5 2.8 3.1 3.5 3.8 3.9 4.1 4.2 4.6 4.8 5.0
do
  sed "s/{{zx}}/$action/g" tracking_script.sad > "$tmp_file"
  echo $action
  #/eos/experiment/fcc/ee/accelerator/SAD/oldsad/bin/gs -env skekb "$tmp_file"
  /home/andym/Documents/SOMA/SAD/bin/gs -env skekb "$tmp_file"
  python make_sdds_from_tracking.py "zx_$action.sdds"
  rm -f "$tmp_file"
  rm -f Outputdata/tracking_{x,y}.tfs
done

set +xe
