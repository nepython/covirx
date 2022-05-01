import requests
import pytz
from difflib import SequenceMatcher
from datetime import datetime

from celery import shared_task
from django.conf import settings

from .utils import target_models, DETAIL_SCRAPING
from .models import Drug, Article

from bs4 import BeautifulSoup

keywords = ['antiviral efficacy', 'antiviral activity', 'in vivo', 'ex vivo']

# construct a dictionary which contains drug name as its key and values as a list target models for which no data

def check_similar(articles, url, title):
    """ Avoid duplicate links """
    for index, article in enumerate(articles):
        if ((SequenceMatcher(a=article['url'],b=url).ratio()>0.9) or
            (SequenceMatcher(a=article['title'],b=title).ratio()>0.98)):
            return index
    return None

def get_articles(keyword, target_model, target_model_attributes, drug_name, from_y, to_y):
    if not DETAIL_SCRAPING:
        URL = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&as_ylo={from_y}&as_yhi={to_y}&q="SARS-CoV-2"+{keyword}+{target_model}+{drug_name}'
    else:
        attributes = ''
        for attr in target_model_attributes:
            attributes += f"'{attr}'+OR+".replace(' (µM)', '').replace(' (nM)', '')
        attributes = attributes[:-4]
        URL = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&as_ylo={from_y}&as_yhi={to_y}&q="SARS-CoV-2"+{keyword}+{target_model}+{drug_name}+{attributes}'
    r = requests.get(URL, allow_redirects=True)
    soup = BeautifulSoup(r.content, 'lxml')
    articles = list()
    for entry in soup.find_all("h3", attrs={"class": "gs_rt"}):
        article = {"title": entry.a.text, "url": entry.a['href']}
        duplicate = check_similar(articles, article['url'], article['title'])
        if duplicate is None:
            articles.append(article)
    return articles


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1000)
def scrape_google_scholar():
    to_y = datetime.now(pytz.timezone(settings.TIME_ZONE)).year
    from_y = to_y-1
    drug_names = {d.name: d for d in Drug.objects.all().order_by('name')}
    drug_names = {d.name: d for d in Drug.objects.filter(name__startswith='Nelfinavir').order_by('name')}
    f_out = open(f"{settings.BASE_DIR}/main/data/scrape_out.csv", 'a')
    queries = [{'k': k, 't': t, 'ta': ta, 'd': d} for k in keywords for t, ta in target_models.items() for d in drug_names.keys()]
    article_count = 0
    for i, q in enumerate(queries):
        articles = get_articles(q['k'], q['t'], q['ta'], q['d'], from_y, to_y)
        for a in articles:
            try:
                article = Article(title=a["title"], url=a["url"], drug=drug_names[q["d"]], target_model=q["t"], keywords=f'{q["k"]}, SARS-CoV-2')
                article.save_and_assign_article(article_count)
                article_count += 1
                f_out.write(f'\"{a["title"]}\", {a["url"]}, {q["d"]}, {q["t"]}, \"{q["k"]}, SARS-CoV-2\"\n')
            except Exception as e:
                print(e)
