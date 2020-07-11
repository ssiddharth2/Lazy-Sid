import os 
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import json
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter

import ssl as ssl_lib
import certifi

ssl_context = ssl_lib.create_default_context(cafile=certifi.where())

app=Flask(__name__)
slacks_events_adaptor=SlackEventAdapter(os.environ['SLACK_SIGNING_SECRET'], "/slack/events", app)

slack_web_client=WebClient(token=os.environ['SLACK_BOT_TOKEN'])

sent =[]
@slacks_events_adaptor.on("message")
def bot_response(payload):
    channel=payload["event"]["channel"]
    message='from the past life'
    #print(payload['event'])
    if 'hi' in payload['event']['text'] and payload['event']['text'] not in sent:
       slack_web_client.chat_postMessage(channel=channel,text=create_message())

def select_random_movies():
    r = requests.get('https://letterboxd.com/s7sid/list/msds-movie-night-list/', headers={"User-Agent": "Mozilla/5.0"})
    content= BeautifulSoup(r.content, 'html.parser')
    list_of_movies=[movie.find('img')['alt']for movie in content.find_all('li',{'class':'poster-container'})]
    movies=np.random.choice(list_of_movies,4,replace=False)
    return movies
def get_metacritic_rating(name, year, is_remake='n'):
    movie_name=meta_critic_name(name)

    url = 'https://www.metacritic.com/movie/' + movie_name
    if(is_remake=='y'):
        url+='-'+ str(year)
    #print(url)
    r = requests.get(url, headers = {"User-Agent": "Safari/601.5.17"})
    s = BeautifulSoup(r.content, 'html.parser')
    try:
        rating=s.find('script',{'type':'application/ld+json'})
        rating=json.loads(rating.get_text())
        rating=rating['aggregateRating']['ratingValue']
        return int(rating)
    except AttributeError:
        return np.NaN
    except KeyError:
        return np.NaN
    except:
        url+='?ref=hp'
        r = requests.get(url, headers={"User-Agent": "Safari/601.5.17"})
        s = BeautifulSoup(r.content, 'html.parser')
        rating = s.find('div', {'class': 'distribution'}).find('div', {'class': 'score fl'})
        rating = rating.find('div', {'class': 'metascore_w larger movie positive'})
        rating = rating.get_text()
        return rating



def meta_critic_name(name):
    name=re.sub(r"[:]", "", name)
    name=re.sub(r"[,]", "", name)
    name=re.sub(r"[&]", "", name)
    #name=re.sub(r"[\-]", "", name)
    name=re.sub(r"[\']", "", name)
    name=re.sub(r"[.]+", "", name)
    name=re.sub(r"[…]", "", name)
    name=name.lower()
    name_lst=name.split()
    addon = ''
    for i in range(len(name_lst)):
        word=name_lst[i]
        if(i!= (len(name_lst)-1)):
            addon += word +'-'
        else:
            addon+=word
    return addon
def rt_url_with_year(movie,year):
    name=re.sub(r"[:]", "", movie)
    name=re.sub(r"[,]", "", name)
    name=re.sub(r"[&]", "", name)
    name=re.sub(r"[\-]", "", name)
    name=re.sub(r"[\']", "", name)
    name=re.sub(r"[.]+", "", name)
    name=re.sub(r"[…]", "", name)
    name=name.lower()
    name_lst=name.split()
    addon = "https://www.rottentomatoes.com/m/"
    addon+= '_'.join(name for name in name_lst)
    return addon+"_"+str(year)

def rt_url(movie):
    name=re.sub(r"[:]", "", movie)
    name=re.sub(r"[,]", "", name)
    name=re.sub(r"[&]", "and", name)
    name=re.sub(r"[\-]", "", name)
    name=re.sub(r"[\']", "", name)
    name=re.sub(r"[.]+", "", name)
    name=re.sub(r"[…]", "", name)
    name=name.lower()
    name_lst=name.split()
    addon = "https://www.rottentomatoes.com/m/"
    addon+= '_'.join(name for name in name_lst)
    return addon
def get_rotten_tomatoes(movie,year):
    try:
        print(rt_url_with_year(movie,year))
        r = requests.get(rt_url_with_year(movie,year), headers={"User-Agent": "Mozilla/5.0"})
        site_content = BeautifulSoup(r.content, 'html.parser')
        site_content_script=site_content.find('script',{'id':'mps-page-integration'})
        pattern=re.compile('window.mpscall =(.*?);')
        score=re.findall(pattern,site_content_script.get_text())[0]
        score=json.loads(score)
        return int(score['cag[score]'])
    except:
        r = requests.get(rt_url(movie), headers={"User-Agent": "Mozilla/5.0"})
        site_content = BeautifulSoup(r.content, 'html.parser')
        site_content_script=site_content.find('script',{'id':'mps-page-integration'})
        pattern=re.compile('window.mpscall =(.*?);')
        try:
            score=re.findall(pattern,site_content_script.get_text())[0]
            score=json.loads(score)
            #print('this is '+score['cag[score]'])
            if score['cag[score]']=='':
                return np.nan
            if score['cag[score]'] is None:
                return np.nan
            return int(score['cag[score]'])
        except:
            return np.NaN

def select_random_movies():
    r = requests.get('https://letterboxd.com/s7sid/list/msds-movie-night-list/', headers={"User-Agent": "Mozilla/5.0"})
    content= BeautifulSoup(r.content, 'html.parser')
    list_of_movies=[movie.find('div')['data-target-link']for movie in content.find_all('li',{'class':'poster-container'})]
    selections=list(np.random.choice(list_of_movies,4,replace=False))
    movies=[]
    years=[]
    for film in selections:
        r= requests.get('https://letterboxd.com{}'.format(film),headers={"User-Agent": "Mozilla/5.0"})
        content= BeautifulSoup(r.content, 'html.parser')
        
        info=content.find('section',{'id':'featured-film-header'})
        movies.append(info.find('h1').getText())
        years.append(info.find('small').getText())
    return movies,years

def create_message():
    message=' /poll "what movie do you want to see tonight" '
    movies,years=select_random_movies()
    for movie, year in zip(movies,years):
        m_rating=get_metacritic_rating(movie,year)
        rt_rating=get_rotten_tomatoes(movie,year)
        message+='"*{}*  Year: {} Metacritic: {} Rotten Tomatoes: {}" '.format(movie,year,str(m_rating),str(rt_rating))
    return message 



if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    app.run(port=3000)