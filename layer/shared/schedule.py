import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta


class Schedule:

    def __init__(self):
        # Get schedule page
        self.url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'
        r = requests.get(self.url)
        # Parse table to json object
        self.soup = [[cell.text or cell.img for cell in row("td")]
                     for row in BeautifulSoup(r.text, 'html.parser')("tr")]
        return

    def extractImage(self, schedule):
        # Extract event image links only
        imagelink = []
        for race in schedule:
            imagetag = str(race)
            m = re.search(r'src=\"(.*)\" ', imagetag)
            imagelink.append(m.group(1))
        # Returning imagelink for debugging
        return imagelink

    def extractInfo(self, schedule):
        # Extract full event info
        eventinfo = []
        for race in schedule:
            event = []
            # Categorize cells
            imagetag = str(race)
            main = str(race[1])
            extra = str(race[2])

            # Imagelink from imagetag
            imagelink = re.search(r'src=\"(.*)\" ', imagetag)

            # Extract date from main
            racedate_m = re.search(
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', main)
            racedate = racedate_m.group()
            date_time_obj = datetime.datetime.strptime(
                racedate, '%Y-%m-%d %H:%M:%S')
            # Convert from UTC to CST
            date_time_obj = date_time_obj - timedelta(hours=5)

            # Grand Prix Name from main
            gp = re.search(r'\n(\w+ GP|\w+ \w+ GP)\n', main)

            # Race Length from extra
            length = re.search(r'Race\sLength:(.*)\n\n\n\n\n', extra)

            # Append to list
            event.append(str(date_time_obj))
            event.append(gp.group(1))
            event.append(length.group(1))
            event.append(imagelink.group(1))
            eventinfo.append(event)
        return eventinfo


class Updater:
    def update():
        return 0


# New Schedule object and do things
schedule = Schedule()
#link = schedule.extractImage(schedule.soup)
info = schedule.extractInfo(schedule.soup)

# Debug output
# - First race
# - List of image links
# - Full event info
# print(schedule.soup[0])
# print(link)
print(info)
