# TODO: Handle case when no network connectivity
# in such cases, an error will be thrown, requests.exceptions.ConnectionError

import requests
from difflib import SequenceMatcher

from django.conf import settings

from .utils import target_model_names
from .models import Drug, Article

from bs4 import BeautifulSoup

from_y = 2021
to_y = 2022
keywords = ['antiviral efficacy', 'antiviral activity', 'in vivo', 'ex vivo']
drug_names = {d.name: d for d in Drug.objects.all().order_by('name')}

# construct a dictionary which contains drug name as its key and values as a list target models for which no data

def check_similar(articles, url, title):
    """ Avoid duplicate links """
    for index, article in enumerate(articles):
        if ((SequenceMatcher(a=article['url'],b=url).ratio()>0.9) or
            (SequenceMatcher(a=article['title'],b=title).ratio()>0.98)):
            return index
    return None

def get_articles(keyword, target_model, drug_name):
    URL = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&as_ylo={from_y}&as_yhi={to_y}&q=%22SARS-CoV-2%22++{keyword}+{target_model}+{drug_name}'
    r = requests.get(URL, allow_redirects=True)
    soup = BeautifulSoup(r.content, 'lxml')
    articles = list()
    for link in soup.find_all('a'):
        url = link.get('href')
        if 'http' not in url or 'scholar.google' in url:
            # TODO: Give a higher priority to journals than preprints
            continue
        req = requests.get(url, allow_redirects=True)
        if 'application/pdf' in req.headers['Content-Type']:
            s = req.headers.get('Content-Disposition', f'"{link.get_text()}"')
            title = s[s.find('"')+1:s.rfind('"')]
        else:
            element = BeautifulSoup(req.content, 'html.parser').select_one('title')
            title = element.text if element is not None else link.get_text()
        duplicate = check_similar(articles, url, title)
        if duplicate is None:
            articles.append({'title':title, 'url': url})
    return articles

f_out = open(f"{settings.BASE_DIR}/main/scrape_out.csv", 'a')
queries = [{'k': k, 't': t, 'd': d} for k in keywords for t in target_model_names for d in drug_names.keys()]
for i, q in enumerate(queries):
    print(i) # Query being scraped
    articles = get_articles(q['k'], q['t'], q['d'])
    for a in articles:
        try:
            a = Article(title=a["title"], url=a["url"], drug=drug_names[q["d"]], target_model=q["t"], keywords=f'{q["k"]}, SARS-CoV-2')
            a.save()
            f_out.write(f'\"{a["title"]}\", {a["url"]}, {q["d"]}, {q["t"]}, \"{q["k"]}, SARS-CoV-2\"\n')
        except:
            pass
