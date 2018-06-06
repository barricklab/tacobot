#!/usr/bin/env bash
cd "${0%/*}"
#Load BOT_ID and SLACK_BOT_TOKEN from untracked file
source secret.txt
source venv/bin/activate
cmd="python tacobot.py"
until $cmd; do
    echo "Slack bot crashed with exit code $?.  Respawning.." >&2
    sleep 1
done
