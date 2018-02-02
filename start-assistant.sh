#!/bin/bash

source /home/pi/env/bin/activate

# set if you are inside firewall
#export http_proxy=http://(proxy server):(port)/
#export https_proxy=http://(proxy server):(port)/
#export ftp_proxy=http://(proxy server):(port)/

python /home/pi/controlTV-ga.py --project_id gatest --device_model_id (id of your model)

