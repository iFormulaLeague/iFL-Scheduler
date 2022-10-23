import requests
import html_to_json


class Ingest:
    def ingest(self):
        # get AM schedule page
        r = requests.get(
            'https://app.xtremescoring.com/api/Embedded/CurrentScheduleDetailed/b21848d5-4f6e-423c-94d7-6c37ab229827/4e9f4c0e-7119-463d-afbf-0347d32bcf26')
        out = html_to_json.convert(r.content)
        return out


class Update:
    def update():
        return 0


i = Ingest()
print(i.ingest())
