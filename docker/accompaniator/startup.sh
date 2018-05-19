#!/bin/bash

# Start fluidsynth
nohup fluidsynth -a alsa -m alsa_seq -l -s -i /usr/share/soundfonts/FluidR3_GM.sf2 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start fluidsynth: $status"
  exit $status
else
  echo "Fluidsynth ran successfully"
fi

cd accompaniator
git checkout ACCOMPANIST-154_site_on_django
cd accompaniator_web

# Start django
nohup python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000 &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start django: $status"
  exit $status
else
  echo "Django ran successfully"
fi

# Start tornado
cd ..
nohup python -m accompaniator_web.tornado_server &
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start tornado: $status"
  exit $status
else
  echo "Tornado ran successfully"
fi

bash
