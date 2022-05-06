import requests
import random
import pytz
from difflib import SequenceMatcher
from datetime import datetime
from time import sleep

from celery import shared_task
from django.conf import settings

from .utils import target_models, DETAIL_SCRAPING
from .models import Drug, Article

from bs4 import BeautifulSoup

# use different user agents to avoid automated request rejection
user_agents = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]
proxies = ['qc', 'phx', 'ny', 'lv', 'fr', 'pl', 'uk', 'lux', 'au', 'sg', 'de']
keywords = ['antiviral efficacy', 'antiviral activity', 'in vivo', 'ex vivo']
PROXY_ENABLED = not settings.DEBUG # don't make proxy request for local development


def _make_proxy_request(URL):
    """
    Google Scholar doesn't allow multiple automated requests
    from the same IP address. To work around it we:
    * use different user-agents
    * use a proxy
    * delay between requests

    Args:
        URL (string): Google Scholar url query

    Returns:
        Response: response object
    """
    sleep(random.randint(1,10)) # sleeps 1-10s before making another request
    headers = {
        'accept': '*/*',
        'User-Agent': random.choice(user_agents),
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en-GB;q=0.9,en;q=0.8',
        'cache-control': 'max-age: 0',
    }
    if PROXY_ENABLED:
        return requests.get(URL, headers=headers, allow_redirects=True)
    proxy_server = "https://www.4everproxy.com/query"
    if not proxies:
        raise ValueError('No working proxy available!')
    selected_proxy = random.choice(proxies)
    data = {
        "allowCookies": "on",
        "customip": "",
        "selip": "random",
        "server_name": selected_proxy,
        "u": URL,
        "u_default": "https://www.google.com"
    }
    try:
        r = requests.post(proxy_server, headers=headers, data=data)
    except requests.exceptions.SSLError as e:
        print(f'\nScraping failed! Internet Service Provider has disabled the proxy server: `{proxy_server}`.\n')
        raise e
    if 'Our systems have detected unusual traffic' in str(r.content):
        # The proxy has been temporarily blocked so don't use it
        proxies.remove(selected_proxy)
        return _make_proxy_request(URL)
    return r


def _clean_url(url):
    """
    If proxy is enabled then the url would be hyperlinked to proxy server.
    Find and return original url
    """
    if not PROXY_ENABLED:
        return url
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    try:
        original_url = soup.find('input', {'id': 'foreverproxy-u'}).get('value')
        return original_url
    except Exception as e:
        print(e)
        return url


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
    r = _make_proxy_request(URL)
    articles = list()
    soup = BeautifulSoup(r.content, 'lxml')
    for entry in soup.find_all("h3", attrs={"class": "gs_rt"}):
        article = {"title": entry.a.text, "url": _clean_url(entry.a['href'])}
        duplicate = check_similar(articles, article['url'], article['title'])
        if duplicate is None:
            articles.append(article)
    return articles


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1000)
def scrape_google_scholar():
    to_y = datetime.now(pytz.timezone(settings.TIME_ZONE)).year
    from_y = to_y-1
    drug_names = {d.name: d for d in Drug.objects.all().order_by('name')}
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
