import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Schedule:

    def __init__(self):
        # GCal Scopes
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        # Get schedule page
        self.xs_url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'
        r = requests.get(self.xs_url)
        # Parse table to json object
        self.soup = [[cell.text or cell.img for cell in row("td")]
                     for row in BeautifulSoup(r.text, 'html.parser')("tr")]
        # Init list of events needing to be updated
        self.events_to_update = []
        # extract info from soup
        self.extract_info()

    def extract_info(self):
        # Extract full event info
        self.event_info = []
        for race in self.soup:
            event = []
            # Categorize cells
            image_tag = str(race)
            main = str(race[1])
            extra = str(race[2])

            # image_link from image_tag
            image_link = re.search(r'src=\"(.*)\" ', image_tag)

            # Extract date from main
            race_date_m = re.search(
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', main)
            race_date = race_date_m.group()
            date_time_obj = datetime.datetime.strptime(
                race_date, '%Y-%m-%d %H:%M:%S')
            # Convert from UTC to CST
            # date_time_obj = date_time_obj - timedelta(hours=5)

            # Grand Prix name from main
            gp = re.search(r'\n(\w+ GP|\w+ \w+ GP)\n', main)

            # Circuit name from main
            circuit = re.search(r'GP\n(.*?)\n', main)

            # Race Length from extra
            length = re.search(r'Race\sLength:(.*)\n\n\n\n\n', extra)

            # Append to list
            event.append(date_time_obj)
            event.append(gp.group(1))
            event.append(circuit.group(1))
            event.append(length.group(1))
            event.append(image_link.group(1))
            self.event_info.append(event)

    def auth_gcal(self):
        # Prints the start and name of the season's events on the iFL AM calendar.
        creds = None
        self.seasonstart = self.event_info[0][0]
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file(
                'token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.creds = creds

    def get_gcal_events(self):
        self.auth_gcal()
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            # Call the Calendar API
            # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            seasonstart = datetime.datetime.isoformat(self.seasonstart) + 'Z'
            print('Getting events from Season Start')
            events_result = service.events().list(calendarId='s1pshnma6bbvuv9lo628cv4heo@group.calendar.google.com',
                                                  timeMin=seasonstart, singleEvents=True, orderBy='startTime').execute()
            races = events_result.get('items', [])
            if not races:
                print('No upcoming events found.')
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                print(calendars)
                return
            self.gcal_events_raw = races
            self.gcal_events = []
            # Prints the start and name of the events
            for race in races:
                event = []
                start = race['start'].get(
                    'dateTime')
                end = race['end'].get('dateTime', race['end'].get('date'))
                summary = race['summary']
                description = race['description']
                location = race['location']
                event.append(start)
                event.append(end)
                event.append(summary)
                event.append(description)
                event.append(location)
                self.gcal_events.append(event)

        except HttpError as error:
            print('An error occurred: %s' % error)

    def compare_schedules(self):
        # Iterate through event_info and gcal_events to find disparities
        count = 0
        for x_race in self.event_info:
            failed = 0
            # Match date string formats and account for timezone offset
            tz_offset = re.search(r'-\d(\d?):', self.gcal_events[count][0])
            tz_offset = tz_offset.group(1)
            newtime = x_race[0] - timedelta(hours=int(tz_offset))
            newtime = str(newtime).replace(' ', 'T')
            newtime = newtime + '-0' + str(tz_offset) + ':00'
            # Compare time strings
            if newtime == self.gcal_events[count][0]:
                print('ITERATION: ', count, ' ', newtime,
                      ' MATCHES ', self.gcal_events[count][0])
            else:
                print('ITERATION: ', count, ' FAIL ', newtime)
                failed = 1

            # Check for GP name
            if x_race[1].lower() in self.gcal_events[count][2].lower():
                print('ITERATION: ', count, ' ',
                      x_race[1], ' MATCHES ', self.gcal_events[count][2])
            else:
                print('ITERATION: ', count, ' FAIL ', x_race[1].lower())
                failed = 1

            # Check locations match
            if x_race[2].lower() in self.gcal_events[count][4].lower():
                print('ITERATION: ', count, ' ',
                      x_race[2], ' MATCHES ', self.gcal_events[count][4])
            else:
                print('ITERATION: ', count, ' FAIL ', x_race[2].lower())
                failed = 1

            # Check race lengths match
            if x_race[3].lower() in self.gcal_events[count][3].lower():
                print('ITERATION: ', count, ' ',
                      x_race[3], ' MATCHES ', self.gcal_events[count][4])
            else:
                print('ITERATION: ', count, ' FAIL ', x_race[3].lower())
                failed = 1

            # Check images match
            if x_race[4].lower() in self.gcal_events[count][3].lower():
                print('ITERATION: ', count, ' ',
                      x_race[4], ' MATCHES ', self.gcal_events[count][3])
            else:
                print('ITERATION: ', count, ' FAIL ', x_race[4].lower())
                failed = 1

            # Add to list of races that don't match, in other words where the Google Calendar is not up-to-date.
            if failed:
                self.events_to_update.append(count)

            count += 1
        return

    def build_gcal_event(self):
        # Assemble Google Calendar events from XtremeScoring schedule information
        return

    def update_gcal_events(self):
        # Update Google calendar events
        return

    def create_gcal_events(self):
        # Create Google calendar events
        return


# New Schedule object and do things
schedule = Schedule()
schedule.get_gcal_events()
schedule.compare_schedules()
print('Events needing an update:', schedule.events_to_update)
