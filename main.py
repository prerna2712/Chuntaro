from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import time
import pyttsx3
import speech_recognition as sr
import pytz
import pickle
import subprocess
import webbrowser
import selenium

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAY_EXTENSIONS = ["nd", "rd", "th", "st"]

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        said = ""

        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))

    return said.lower()    

def authenticate_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    return service


def get_events(day,service):
    date = datetime.datetime.combine(day,datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day,datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(), singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found sir.')
    else:
        speak(f"You have {len(events)} events on this day sir")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split(":")[0])
            if int(start_time.split(':')[0])<12:
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) + start.split("T")[1].split(":")[1]
                start_time = start_time + "pm"

            speak(event["summary"] + " at " + start_time)

def get_date(text):
    text=text.lower()
    today = datetime.date.today()
    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word)+1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                found = word.find(ext)
                if found > 0:
                    try: 
                        day = int(word[:found])
                    except:
                        pass

    if month < today.month and month != -1:
        year = year+1
    if day<today.day and month == -1 and day != -1:
        month = month+1
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week
        if dif<0:
            dif+=7
            if text.count("next")>=1:
                dif+=7
        return today+datetime.timedelta(dif)
    if month == -1 or day == -1:
        return None
        
    return datetime.date(month=month,day=day,year=year)

def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name,"w") as f:
        f.write(text)

    subprocess.Popen(["gedit", file_name])


WAKE = "ron"
SERVICE = authenticate_google()
print("Start")

while True:
    print("Listening")
    text = get_audio().lower()

    if text.count(WAKE)>0 :
        speak("Ready sir")
        text = get_audio()
        if text.count("open")>0 :
            if "open youtube" in text:
                webbrowser.open("youtube.com")

            elif 'open google' in text:
                webbrowser.open("google.com")    
                 
            elif 'stack overflow' in text:
                webbrowser.open("stackoverflow.com/")

            elif 'github' in text:
                webbrowser.open("github.com")    

            elif 'leetcode' in text:
                webbrowser.open("leetcode.com")

            elif 'codechef' in text:
                webbrowser.open("codechef.com")

            elif 'codeforces' in text:
                webbrowser.open("codeforces.com")

            elif 'netflix' in text:
                webbrowser.open("netflix.com")

            elif 'facebook' in text:
                webbrowser.open("facebook.com")

            elif 'instagram' in text:
                webbrowser.open("instagram.com")  

        CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy", "do i have anything on"]
        for phrase in CALENDAR_STRS:
            if phrase in text.lower():
                date = get_date(text)
                print(date)
                if date:
                    get_events(date,SERVICE)
                else:
                    speak("I don't understand, my apologies sir")

        NOTE_STRS = ["take a note", "write this down", "remember this"]
        for phrase in NOTE_STRS:
            if phrase in text:
                speak("What would you like me to write down sir?")
                note_text = get_audio().lower()
                note(note_text)
                speak("I've made a note of that.")

    if text.count("stop") > 0:
        break