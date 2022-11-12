# iFL-Scheduler [![CodeQL](https://github.com/jbies121/iFL-Scheduler/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/jbies121/iFL-Scheduler/actions/workflows/codeql.yml)

Scheduling automation for the iFormula League

## Setup

### Requirements

```text
XtremeScoring Series and Schedule
Google Calendar
Google Calendar API
    - Configured OAuth Screen
    - OAuth Credentials (JSON format, save in layer/shared/credentials.json)
```

### First Run

On first run with a new token, you will be required to authenticate via a webbrowser.

Set xs_url in the Schedule object to your XtremeScoring 'Current Schedule (Detailed)' Web Widget.

Set calendar_id in the Schedule object to the Google Calendar to be synced to your XtremeScoring schedule.

```python
def __init__(self):
    ...
    self.calendar_id = 'xxxxxxxxxxxxxxxxxxxxxxxxxx@group.calendar.google.com'
    ...
    self.xs_url = 'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
    ...
```

This can be run on a schedule task to keep your Google calendar synced to your XtremeScoring schedule.
