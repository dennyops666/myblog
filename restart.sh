#!/bin/bash
pkill -f gunicorn
sleep 2
gunicorn wsgi:application --bind 0.0.0.0:5000 --workers 1 --timeout 120 --reload --daemon --pid /data/myblog/app.pid --log-file /data/myblog/logs/myblog.log --error-logfile /data/myblog/logs/error.log --log-level debug
