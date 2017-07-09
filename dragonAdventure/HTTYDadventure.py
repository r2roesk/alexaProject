"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import boto3
import json
import decimal
import time
import calendar
from boto3.dynamodb.conditions import Key, Attr


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

# --------------- Interacting with DynamoDB ------------------------------------
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('HTTYDAdventure')
epoch_time = int(time.time())

def feed_Dragon():

    dragonID = "Toothless"
    response = table.get_item(
        Key={
            'dragonID': dragonID
        }
    )

    hunger_level = response['Item']['hunger']
    if hunger_level < 5:

        hunger_level += 1
        response = table.update_item(
            Key={
                'dragonID': dragonID
            },
            UpdateExpression="set hunger = :h, sleepiness =: s",
            ExpressionAttributeValues={
                ':h': decimal.Decimal(hunger_level),
                ':s': decimal.Decimal(4)
            },
            ReturnValues="UPDATED_NEW"
        )
        return "Fed him and now your dragon is at hunger level " + str(hunger_level)

    else:
        return "Uh oh. Your dragon is full."

def get_names():
    names = ""

    response = table.scan()
    nameCount = len(response['Items'])

    for idx, item in enumerate(response['Items']):
        names += item['dragonID']
        if idx == nameCount - 2:
            names += " and "
        elif idx != nameCount - 1:
            names += ", "

    return names

def get_stats():

    dragonID = "Toothless"
    response = table.get_item(
        Key={
            'dragonID': dragonID
        }
    )

    hunger_level = response['Item']['hunger']
    sleepiness_level = response['Item']['sleepiness']

    return "Your dragon's hunger level is " + str(hunger_level) + "and the sleepiness level is " + str(sleepiness_level)


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
    speech_output = """Welcome to the How to Train Your Dragon Adventure.
                    An alexa skill made for the Intern Project by the Mediatechos team."""
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_feeding_response():
    session_attributes = {}
    card_title = "Feeding"
    speech_output = feed_Dragon()
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_stats_response():
    session_attributes = {}
    card_title = "Stats"
    speech_output = get_stats()
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))

def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


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
    if intent_name == "FeedIntent":
        return get_feeding_response()
    elif intent_name == "StatsIntent":
        return get_stats_response()
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
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
