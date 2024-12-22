#!/usr/bin/env bash
gunicorn farmhelp.wsgi:application --bind 0.0.0.0:$PORT
