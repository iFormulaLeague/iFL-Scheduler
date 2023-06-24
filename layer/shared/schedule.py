import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
from dateutil import parser
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Schedule:

    def __init__(self, series):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
                       'https://www.googleapis.com/auth/calendar']
        if (series == 'F1'):
            self.series = 'F1'
            # F1 Series Duration (Hours)
            self.delta = 3
            # F1 Calendar ID
            self.calendar_id = 'gkpqcb2iskomkm6tl3bo7fvat4@group.calendar.google.com'
            # Get F1 schedule page
            self.xs_url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/2e274914-e1e0-4fdd-bf2f-d8a74c46068a'
        if (series == 'F3'):
            self.series = 'F3'
            # F1 Series Duration (Hours)
            self.delta = 2.5
            # F3 Calendar ID
            self.calendar_id = 's1pshnma6bbvuv9lo628cv4heo@group.calendar.google.com'
            # Get F3 schedule page
            self.xs_url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'
        if (series == 'F4'):
            self.series = 'F4 Developmental'
            # F4 Series Duration (Hours)
            self.delta = 2.5
            # F4 Calendar ID
            self.calendar_id = '3508c492264665903c401c588e716972f95c2f473d9edb69ff66d06882f17df5@group.calendar.google.com'
            # Get F4 schedule page
            self.xs_url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'

        self.UTC_tz = pytz.timezone('UTC')

        # Scrape Xtremescoring Schedule
        r = requests.get(self.xs_url)
        # Parse table to json object
        self.soup = [[cell.text or cell.img for cell in row("td")]
                     for row in BeautifulSoup(r.text, 'html.parser')("tr")]
        # Init list of events needing to be updated
        self.events_to_update = []
        self.events_to_create = []
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

            # Extract date from main and convert UTC timezone
            race_date_m = re.search(
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', main)
            race_date = race_date_m.group()
            date_time_obj = datetime.datetime.strptime(
                race_date, '%Y-%m-%d %H:%M:%S')
            utc_dt = self.UTC_tz.localize(date_time_obj)

            # Grand Prix name from main
            gp = re.search(r'\n.+?\n([\w\d -\/]+)\n', main)

            # Circuit name from main
            circuit = re.search(r'\n.+?\n.+?\n([\w\d -\/]+)\n', main)

            # Race Length from extra
            length = re.search(r'Race\sLength:(.*?)\n', extra)

            # Append to list
            event.append(utc_dt)
            event.append(gp.group(1))
            event.append(circuit.group(1))
            event.append(length.group(1))
            event.append(image_link.group(1))
            self.event_info.append(event)

    def auth_gcal(self):
        # Prints the start and name of the season's events on the iFL AM calendar.
        creds = None
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
        service = build('calendar', 'v3', credentials=self.creds)
        try:
            # Call the Calendar API
            # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            if (self.series == "F4 Developmental"):
                seasonstart = self.event_info[0][0] + timedelta(days=-1,hours=3)
                seasonstart = seasonstart.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                seasonstart = self.event_info[0][0].strftime('%Y-%m-%dT%H:%M:%SZ')
                
            print('Getting events from ' + self.series + ' Season Start')
            events_result = service.events().list(calendarId=self.calendar_id,
                                                  timeMin=seasonstart, singleEvents=True, orderBy='startTime').execute()
            races = events_result.get('items', [])
            # List calendars if no events found
            if not races:
                print('No upcoming events found.')
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get('items', [])
                print(calendars)
                return
            self.gcal_events_raw = races
            self.gcal_events = []
            # Create a list of lists of event data matching the format from the scraped XtremeScoring schedule
            for race in races:
                event = []
                # Parse datetimes and convert to UTC isoformat
                start = race['start'].get(
                    'dateTime')
                start = parser.parse(start)
                start = start.astimezone(self.UTC_tz).isoformat()
                end = race['end'].get('dateTime', race['end'].get('date'))
                end = parser.parse(end)
                end = end.astimezone(self.UTC_tz).isoformat()
                # Parse remaining text
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
        self.times_iso = []
        for x_race in self.event_info:
            times = []
            failed = 0
            # Derive endtime and convert to isoformat
            # endtime timedelta must be adjusted manually based on series event duration.
            # This is a limitation due to data availablility from the detailed schedule view in XS.
            endtime = x_race[0] + timedelta(hours=self.delta)
            newtime = x_race[0]
            # F4 follows exact format of F3 but is run at a different time, so 
            if (self.series == "F4 Developmental"):
                endtime = endtime + timedelta(days=-1,hours=3)
                newtime = newtime + timedelta(days=-1,hours=3)
            # convert to isoformatted strings and append to arrays so they can be used in comparison and event creation
            newtime = newtime.isoformat()
            endtime = endtime.isoformat()
            times.append(newtime)
            times.append(endtime)
            self.times_iso.append(times)
            try:
                # Compare time strings
                if newtime != self.gcal_events[count][0]:
                    print('ITERATION: ', count, ' UPDATE ',
                          newtime, self.gcal_events[count][0])
                    failed = 1

                # Check for GP name
                if x_race[1].lower() not in self.gcal_events[count][2].lower():
                    print('ITERATION: ', count, ' UPDATE ', x_race[1].lower())
                    failed = 1

                # Check locations match
                if x_race[2].lower() not in self.gcal_events[count][4].lower():
                    print('ITERATION: ', count, ' UPDATE ', x_race[2].lower())
                    failed = 1

                # Check race lengths match
                if x_race[3].lower() not in self.gcal_events[count][3].lower():
                    print('ITERATION: ', count, ' UPDATE ', x_race[3].lower())
                    failed = 1

                # Check images match
                if x_race[4].lower() not in self.gcal_events[count][3].lower():
                    print('ITERATION: ', count, ' UPDATE ', x_race[4].lower())
                    failed = 1

                # Add to list of races that don't match, in other words where the Google Calendar is not up-to-date.
                if failed:
                    self.events_to_update.append(count)

                count += 1
            except (IndexError,AttributeError):
                self.events_to_create.append(count)
                count += 1

        if self.events_to_update:
            print('Events needing an update: ', self.events_to_update)
            self.update_gcal_events()
        else:
            print('No events needing an update.')

        if self.events_to_create:
            print('Events to be created: ', self.events_to_create)
            self.create_gcal_events()
        else:
            print('No events needing to be created.')

    def build_gcal_events(self, events_to_do):
        # Assemble Google Calendar events from XtremeScoring schedule information
        events = []
        for race in events_to_do:
            racenumber = str(race + 1)
            summary = 'iFL ' + self.series + ' - Round ' + \
                racenumber + ' - ' + self.event_info[race][1]
            location = self.event_info[race][2]
            description = '+++<br>cover="<a href="' + self.event_info[race][4] + '">' + self.event_info[race][4] + '</a>"<br>+++<br><br>Round ' + \
                racenumber + ' of the iFL ' + self.series + ' Championship<br>' + \
                self.event_info[race][3] + '<br><html-blob><u></u></html-blob>'
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': str(self.times_iso[race][0]),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': str(self.times_iso[race][1]),
                    'timeZone': 'UTC',
                },
            }
            events.append(event)
        return events

    def update_gcal_events(self):
        # Update Google calendar events
        # Build new event
        event = self.build_gcal_events(self.events_to_update)
        for index in range(len(event)):
            # Get existing event
            existing_event = self.gcal_events_raw[index]
            # Push Update
            service = build('calendar', 'v3', credentials=self.creds)
            updated_event = service.events().update(
                calendarId=self.calendar_id, eventId=existing_event['id'], body=event[index]).execute()
            print(updated_event['updated'])

    def create_gcal_events(self):
        # Create Google calendar events
        # Build an event
        event = self.build_gcal_events(self.events_to_create)
        for index in range(len(event)):
            # Create a gcal event
            service = build('calendar', 'v3', credentials=self.creds)
            new_event = service.events().insert(
                calendarId=self.calendar_id, body=event[index]).execute()
            print('Event created: %s' % (new_event.get('htmlLink')))


# New Schedule object and do things
schedule = Schedule('F3')
schedule.get_gcal_events()
schedule.compare_schedules()

# Create a schedule object for a second series.
schedule = Schedule('F1')
schedule.get_gcal_events()
schedule.compare_schedules()

# Create a schedule object for a third series.
schedule = Schedule('F4')
schedule.get_gcal_events()
schedule.compare_schedules()