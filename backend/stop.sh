#!/bin/bash
kill ` ps -A | grep "gunicorn" | cut  -d " " -f 1,2`
# kill ` ps -A | grep "uvicorn" | cut  -d " " -f 1,2`
# sleep 1
