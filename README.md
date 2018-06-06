# Barrick Lab Slack Tacobot

## Setup

Create a file `secret.txt` that contains `BOT_ID` and `SLACK_BOT_TOKEN`
```
xport BOT_ID='XXXXXXX'
export SLACK_BOT_TOKEN='XXXXXXX'
```

Create the virtual environment and install required modules:
```
virtualenv venv
pip install -r requirements.txt
```

Authorize the bot to receive messages from Slack.
