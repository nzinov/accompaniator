#!/bin/bash

# Start the first process
nohup fluidsynth -a alsa -m alsa_seq -l -s -i /usr/share/soundfonts/FluidR3_GM.sf2 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start fluidsynth: $status"
  exit $status
else
  echo "Fluidsynth ran successfully"
fi

python3 web/tornado_server.py

bash