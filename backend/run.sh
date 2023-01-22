#!/bin/bash
export SEC_KEY=` openssl rand -hex 10`
export WEB_CONCURRENCY=`nproc`
kill ` ps -A | grep "gunicorn" | cut  -d " " -f 1,2`
# kill ` ps -A | grep "uvicorn" | cut  -d " " -f 1,2`
sleep 1
gunicorn wsgi:app --timeout 600 
# sleep 1
# uvicorn --port 9000 unicorn:api &
