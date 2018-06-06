#!/usr/bin/env bash
export SLACK_BOT_TOKEN='xoxb-195800743191-af1II1XuHe50kdqBelF7d7eh'
export BOT_ID='U5RPJMV5M'
source /home/web/tacobot/virtualenv/bin/activate
cmd="python /home/web/tacobot/tacobot.py"
until $cmd; do
    echo "Slack bot crashed with exit code $?.  Respawning.." >&2
    sleep 1
done
