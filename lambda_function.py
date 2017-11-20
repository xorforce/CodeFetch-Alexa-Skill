from __future__ import print_function
import requests
import json
import os
import sys
import urllib
import bs4 from BeautifulSoup

# --------------- Helpers that build all of the responses ----------------------
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to Code Fetch. Tell me to fetch anything from the web."
    reprompt_text = "Hi, tell me to fetch a code, and I'll get it for you."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
def fetchCode(intent, session):
    
    if "algorithm" in intent['slots'] and "language" in intent['slots']:
        algorithm = intent['slots']['algorithm']
        language = intent['slots']['language']
        
    #scrape done
    code = scrapeData(intent, session, algorithm, language)

    if code != -1:
        
        #send code to pastebin api
        api_dev_key = getApiKey()
        #steps
        # 1. Create user session key
        user_key = createUserKey(api_dev_key)

        # 2. Create Paste and get url back for future reference
        paste_key = pasteDataAndGetPasteKey(api_dev_key, user_key, language, code)

        # 3. Done. 

        # 4. Send key to our own api
        postDataToOwnApi(paste_key)

        # 5. Api Workflow Ends

        #TO DO :- Do rest of work
    
        #build success response here
        speech_output = "Your program was found successfully. Please check out the work on your computer.;"
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))
    else:
        speech_output = "A suitable code was not found. Please try again."
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you" \
                    "Have a nice day! "
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# --------------- Helper Functions ---------------

def scrapeData(intent, session, algorithm, language):
    query = '{} in {} site:stackoverflow.com'.format(algorithm, language)
    query = query.replace(" ", "+")
    google_url = "https://www.google.com/search?q="+query
    request = urllib.request.Request(google_url,headers={'User-Agent':'Sublime Text'})
    r = urllib.request.urlopen(request).read()
    soup = BeautifulSoup(r, "html.parser")

    for item in soup.find_all('h3', attrs={'class' : 'r'}):
		first_url = item.a['href'][7:]
		break

    response = urllib.request.urlopen(first_url).read()
    soup = BeautifulSoup(response, "html.parser")

    for item in soup.find_all('div', attrs={'class' : 'answer'}):
		try:
			code = item.find('pre').find('code').text
			return code
		except:
			continue
return -1


def createUserKey(api_dev_key):
    
    username = 'bhagat'
    password = 'heylo123'

    user_key_data = {'api_dev_key':api_dev_key,'api_user_name':username,'api_user_password'}
    req = urllib2.urlopen('https://pastebin.com/api/api_login.php', urllib.urlencode(user_key_data).encode('utf-8'), timeout=7)
    user_key = (req.read().decode())
    return user_key

def pasteDataAndGetPasteKey(api_dev_key, user_key, language, code):
    api_option = 'paste'
    api_paste_code = code
    api_paste_format = language.lower()
    api_paste_expire_date = 'N'
    api_paste_private = 0
    data = {'api_dev_key':api_dev_key,'api_option':api_option,'api_user_key': user_key,'api_paste_code': api_paste_code,
    'api_paste_format':api_paste_format,'api_paste_expire_date':api_paste_expire_date, 'api_paste_private':api_paste_private}
    req = urllib2.urlopen('https://pastebin.com/api/api_post.php', urllib.urlencode(data).encode('utf-8'),timeout=7)
    paste_key = req.read()
    paste_key = paste_key.replace("https://pastebin.com/", "")
    return paste_key

def postDataToOwnApi(paste_key):
    url = ''
    post_data = {"paste_key":paste_key}
    #req = requests.post(url, data = post_data)
    #req = req.json()

def getApiKey():
    return 'caa5022193a9ddc384001521968843ad'


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "FetchCode":
        return fetchCode(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])