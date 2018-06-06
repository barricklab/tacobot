import os
import sys
import time
import csv
import pprint
import re
import pickle
import time

from slackclient import SlackClient

# tacobot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

TACO_FILE_PATH = os.path.dirname(os.path.abspath(sys.argv[0])) + "/" + "taco.csv"
TACO_USER_PICKLE_PATH = os.path.dirname(os.path.abspath(sys.argv[0])) + "/" + "taco_users.pkl"
TACO_HEADER_LIST = ['user_id', 'current_tacos', 'all_time_tacos']
TACO_AUTHORIZED_USER_NAMES = ['simonvdalton', 'jbarrick']
NUM_TACOS_TO_REDEEM = 3

USER_INFO = {}
USER_INFO_LAST_SLACK_LOAD_TIME = 0
USER_INFO_SLACK_RELOAD_TIME = 600 #10 minutes
BOT_USER_NAME = "tacobot"

#Looks up info about a specific user.
#Reloads info from Slack if a certain amount of time has passes
#Otherwise uses a picked version
def load_user_info():
    global USER_INFO
    global USER_INFO_LAST_SLACK_LOAD_TIME
    reload = 0
    if not os.path.isfile(TACO_FILE_PATH) or (time.time() - USER_INFO_LAST_SLACK_LOAD_TIME > USER_INFO_SLACK_RELOAD_TIME):
       USER_INFO_LAST_SLACK_LOAD_TIME = time.time()
       reload = 1
    
    #undefined, missing
    if reload==1:
        print "***Reloading user list from Slack\n"
        r = slack_client.api_call(
            "users.list",
        )
        pickle.dump( r['members'], open( TACO_USER_PICKLE_PATH, "wb" ) )
    else:
        print "***Using cached user list\n"
        
    print "*Loading user list from file\n"
    USER_INFO = pickle.load( open( TACO_USER_PICKLE_PATH, "rb" ) )
    
    #pprint.pprint(USER_INFO)

def read_tacos():
    #does it exist?
    if not os.path.isfile(TACO_FILE_PATH):
        return {}
        
    tacos = {}
    with open(TACO_FILE_PATH, 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            print(row)
            tacos[row['user_id']] = row 
          
    return tacos


    
def write_tacos(tacos):
    #does it exist?
    with open(TACO_FILE_PATH, 'w') as csvfile:
        csv_writer = csv.DictWriter(csvfile, ['user_id', 'current_tacos', 'all_time_tacos'])
        csv_writer.writeheader()
        for key in tacos:
            taco_line = tacos[key]
            taco_line['user_id'] = key
            csv_writer.writerow(taco_line)

    

def get_name_to_user_id_lookup_table():
    global USER_INFO
    load_user_info()
    name_to_user_id_lookup_table = {}
    for member in USER_INFO:
      name_to_user_id_lookup_table[member['name']] = member['id']
      

    return name_to_user_id_lookup_table
    
def get_user_id_to_name_lookup_table():
    global USER_INFO
    load_user_info()
    user_id_to_name_lookup_table = {}
    for member in USER_INFO:
      user_id_to_name_lookup_table[member['id']] = member['name']
        
    #pprint.pprint(user_id_to_name_lookup_table)
    return user_id_to_name_lookup_table
    
    
def handle_command(command, channel, user):
    global BOT_USER_NAME
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    user_id_to_name_lookup_table = get_user_id_to_name_lookup_table()
    
    print command
    user_id = ""
    pattern = re.compile(r'<@(\S+)>')
    user_id_match = re.search(pattern, command)
    if user_id_match:
        user_id = user_id_match.group(1).upper()
    
    
    print user_id
    
    if (command.count("standings")):
        tacos = read_tacos()
        
        message = "user current [all-time]\n"
        for user_id in tacos:
            entry = tacos[user_id]
            #pprint.pprint(entry)
            message += user_id_to_name_lookup_table[entry['user_id']] + " " + entry['current_tacos'] + " [" + entry['all_time_tacos'] + "]\n"
        
        slack_client.api_call(
            "chat.postMessage",
            icon_emoji=":trophy:",
            username="Taco Point Standings",
            channel=channel,
            text= message,
            as_user=False
        )
        return
    
    user_id_to_name_lookup_table = get_user_id_to_name_lookup_table()
    calling_user_name = user_id_to_name_lookup_table[user]
    if not calling_user_name in TACO_AUTHORIZED_USER_NAMES:
    
    
        if calling_user_name=="spleonard1":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text= "Not you again! AAAAAAHHHHH!",
                as_user=True
            )
        else:
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text= "Nice try! You are not authorized to give/redeem taco points.",
                as_user=True
            )
        return
    # Did we find a valid username?
    # The first one in the line is the one we will give tacos to
    if user_id:
        num_tacos = command.count(":taco:")
        if num_tacos > 0:
            
            tacos = read_tacos()
            if (not user_id in tacos):
                tacos[user_id] = {'user_id' : user_id, 'current_tacos' : 0, 'all_time_tacos' : 0}
                    
            num_redeem = command.count("redeem")
            if num_redeem > 0:
                
                if int(tacos[user_id]['current_tacos']) < 3:
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text= ("You need " + str(NUM_TACOS_TO_REDEEM) + " taco points to redeem!\n" + 
                        "(" + tacos[user_id]['current_tacos'] + " in the bank and " + tacos[user_id]['all_time_tacos'] + " all-time.)"),
                        as_user=True
                    )
                    return
                else:
                    tacos[user_id]['current_tacos'] = str(int(tacos[user_id]['current_tacos']) - NUM_TACOS_TO_REDEEM)
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text= (":taco: CONG :taco: RATU :taco:  <@" + user_id + "> :taco: LATI :taco: IONS! :taco:\n" + 
                        "(" + tacos[user_id]['current_tacos'] + " in the bank and " + tacos[user_id]['all_time_tacos'] + " all-time.)"),
                        as_user=True
                    )
                write_tacos(tacos)

            else:
                if (not user_id in tacos):
                    tacos[user_id] = {'user_id' : user_id, 'current_tacos' : 0, 'all_time_tacos' : 0}
                tacos[user_id]['current_tacos'] = str(int(tacos[user_id]['current_tacos']) + num_tacos)
                tacos[user_id]['all_time_tacos'] = str(int(tacos[user_id]['all_time_tacos']) + num_tacos)
                write_tacos(tacos)
            
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text= ("<@" + user_id + "> earned " + str(num_tacos) + " taco point" + ( "s" if (num_tacos>1) else "") + "!\n" + 
                    "(" + tacos[user_id]['current_tacos'] + " in the bank and " + tacos[user_id]['all_time_tacos'] + " all-time.)"),
                    as_user=True
                )
        
            
    
    #for (user_id) in re.findall(pattern, command):
    #    user_id = user_id.upper()
        #slack_client.api_call(
        #    "chat.postMessage",
        #    channel=channel,
        #    text= user_id + " = " + user_id_to_name_lookup_table[user_id],
        #    as_user=True
        #)
    
    
    slack_client.api_call(
      "chat.postMessage",
      channel=channel,
      text="Hello from :taco: land!",
      as_user=True
    )


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            #pprint.pprint(output)
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], output['user']
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("tacobot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

