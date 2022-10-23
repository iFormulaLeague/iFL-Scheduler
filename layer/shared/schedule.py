import requests
from bs4 import BeautifulSoup
import re


class Schedule:
    url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26'

    def __init__(self):
        # get schedule page
        r = requests.get(self.url)
        # parse table to json object
        self.out = [[cell.text or cell.img for cell in row("td")]
                    for row in BeautifulSoup(r.text, 'html.parser')("tr")]
        return

    def extractImage(self, schedule):
        # Extract event image
        imagelink = []
        for race in schedule:
            imagetag = str(race[0])
            m = re.search(r'src=\"(.*)\" ', imagetag)
            imagelink.append(m.group(1))
        # returning imagelink for debugging
        return imagelink


class Updater:
    def update():
        return 0


# new Schedule object and do things
schedule = Schedule()
link = schedule.extractImage(schedule.out)

# debug output
# - first race
# - list of image links
print(schedule.out[0])
print(link)
