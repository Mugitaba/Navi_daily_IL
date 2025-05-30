import os
import requests
import xmltodict
import json
import google.generativeai as genai
from gtts import gTTS
from datetime import datetime
from flask import Flask




YNET_URL = 'https://www.ynet.co.il/Integration/StoryRss1854.xml'
WALLA_URL = 'https://rss.walla.co.il/feed/22'
HAARETZ_URL = 'https://www.haaretz.co.il/srv/rss---feedly'
NYT_URL = 'https://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml'
MAARIV_URL = 'https://www.maariv.co.il/Rss/RssFeedsMivzakiChadashot'


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

now = datetime.now()
today_date_time = now.strftime("%Y_%m_%d-%H")
audio_file_path = f"static/news{today_date_time}.mp3"

LLM_HEADERS = {
    "Content-Type": "application/json"
}

web_app = Flask(__name__)


class Source:
    def __init__(self, name, url, roots):
        self.name = name
        self.url = url
        self.roots = roots


ynet = Source('Ynet', YNET_URL, False)
walla = Source('Walla', WALLA_URL, False)
haaretz = Source('Haaretz', HAARETZ_URL, False)
nyt = Source('New York Times', NYT_URL, False)
maariv = Source('Maariv', MAARIV_URL, False)

sites_list = [ynet, walla, haaretz, nyt, maariv]
full_headlines = {}

for single_site in sites_list:
    full_headlines[single_site.name] = []

def get_rss_response(site):
    if not site.roots:
        rss_response = requests.get(site.url).text
        res = xmltodict.parse(rss_response)['rss']['channel']['item']
    # for root in site.roots:
    #     print(root, res.keys())
    #     res = res[root]
    else:
        res = None
    return res


def print_rss_reults(site):
    content = get_rss_response(site)

    for item in content:
        full_headlines[site.name].append(f'title: {item["title"]}\npublished:{item["pubDate"]}\nlink:{item["link"]}\n\n')


for news_site in sites_list:
    print_rss_reults(news_site)

LLM_CONTENT = "You are a personal assistant assigned with giving a quick daily summary of the day's headlines in Israel."\
              "Here are today's headlines and links. Please sum them all up to a one-pager cohesive narrative describing the day's events.\n"\
              "*Impotant notes:** Write in the form od an essay, not in bullet points. Take the publication time into account. if there are any discrepancies between sources, mention which source says what"\
              f"and how they contradict please.\n {json.dumps(full_headlines, ensure_ascii=False)}"

response = model.generate_content(LLM_CONTENT)

essay = response.text.replace('#', '').replace('*', '')
html_essay = essay.replace('\n', '<br>')

print(essay)

if not os.path.exists(audio_file_path):
    if not os.path.exists('static'):
        os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
    tts = gTTS(text=essay, lang='en')
    tts.save(audio_file_path)


@web_app.route('/')
def index():
    return f'''
    <!DOCTYPE html>
        <html lang=en>
            <h1>Today's news Summary{today_date_time}</h1>
            <p>{html_essay}</p>
            <audio controls src="{audio_file_path}">
            </audio>
        </html>

    '''


if __name__ == '__main__':
    web_app.run(host='0.0.0.0', port=5000, debug=True)
