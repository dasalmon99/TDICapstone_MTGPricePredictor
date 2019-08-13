import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import matplotlib.pyplot as plt
from time import sleep
import datetime as dt
from os import system

def getdecklist(deckid):
    """Returns a dataframe of the decklist (deckid) on mtggoldfish,
containing only cardname and quantity data."""
    #Note: only works for decks containing 75 cards
    
    with requests.get('https://www.mtggoldfish.com/deck/'+ str(deckid)) as r:
    

        soup = BeautifulSoup(r.text,'html.parser')
        quant = []
        deck = []
        tdqty = soup.findAll(lambda tag: tag.name == "td" and tag.get('class') == ['deck-col-qty']) 
        tdcard = soup.findAll(lambda tag: tag.name == "td" and tag.get('class') == ['deck-col-card'])
        for card in tdcard:
            deck.append(card.text.strip())

        for qty in tdqty:
            if sum(quant) < 75:
                quant.append(int(qty.text.strip()))
        deck = deck[0:len(quant)]
        df = pd.DataFrame({'Card':deck, 'Quantity':quant})
        df.Quantity = df.Quantity.astype('int64')
        df.Card = df.Card.astype(str)
        
        df_list = [[row[1]['Card'], row[1]['Quantity']]  for row in df.iterrows()]        
        
        return df_list

def getdecks(tournament_name):
    """Returns a list of each deckid that is on the tournament page of tournament_name"""
    
    with requests.get('https://www.mtggoldfish.com/tournament/' + str(tournament_name)) as r:
        deckids = []
        soup = BeautifulSoup(r.text, 'html.parser')
        tddeckid = soup.findAll("td", {'class': 'text-right tournament-decklist-toggle'})
        for deck in tddeckid:
            deckids.append(int(deck['data-deckid']))
        return deckids

def get_price_history(expansion, card_name):
    """Returns daily price history of card from mtggoldfish (must include expansion/printing)"""
    
    expansion = expansion.replace(' ','+').replace(':','')    
    card_name = card_name.replace(' ','+').replace('\'', '').replace(',','')
    with requests.get('https://www.mtggoldfish.com/price/'+expansion+'/'+card_name) as r:

        #drop online prices from being found by regex
        drop_point = '$(".price-sources-online").toggle(true)'
        indx = r.text.find(drop_point)
        search_text = r.text[:indx]
        
        pattern = '\d{4}-\d{2}-\d{2}\,\s\d+\.\d+'
        dates_price = re.findall(pattern,search_text)
        date = []
        price = []
        for entry in dates_price:
            if entry[0:10] not in date:
                date.append(entry[0:10])
                price.append(entry[12:])

        df = pd.DataFrame({'Date':date, 'Price':price})
        df['Date'] = df['Date'].astype('datetime64[ns]')
        df['Price'] = df['Price'].astype('float')
        return df

def scrape_tourney(tournament_name):
    """ Returns metadata (list of decklists and a card_totals dataframe) from tournament name on mtggoldfish"""

    deckids = getdecks(tournament_name)
    sleep(2)
    decklists = []
    if not deckids:
        return decklists
    else:
        for deck in deckids:
            df = getdecklist(deck)        
            decklists.append(df)
            print('getting deck ' + str(deck) + '...')
            sleep(2)
    
        #tmp = pd.concat(decklists)
        #card_totals = tmp.groupby(by = 'Card', as_index = False)['Quantity'].sum()
        return decklists

def scrape_results_page(url):
    """Returns dataframe of tournaments listed on a search results page url. Returns decklists, date, tournament_id"""

    with requests.get(url) as r:
        tourney_list = []
        date_list = []
        soup = BeautifulSoup(r.text, 'html.parser')
        tourney_tags = soup.findAll("a", href=lambda href: href and "/tournament/" in href)
        pattern = '\d{4}-\d{2}-\d{2}'
        date_tags = soup.findAll("td", text=lambda text: re.match(pattern,text))
        for tourn in tourney_tags:
            tourney_list.append(tourn['href'][12:])
        for day in date_tags:
            date_list.append(day.text)

        df_tourneys = pd.DataFrame()
        for idx, tourn in enumerate(tourney_list):
            print('Scraping tournament: ' + tourn)
            decks = scrape_tourney(tourn)
            df_tourneys = df_tourneys.append({'Date':pd.to_datetime(date_list[idx]), 'id_num': tourn, 'Decks':decks}, ignore_index=True)
            sleep(5)
            system('clear')            
        return df_tourneys

def scrape_meta(start, stop):
    """Scrapes Tournament data for pages in page range. Manually adjust url for search result landing"""

    begin_url = 'https://www.mtggoldfish.com/tournament_searches/create?commit=Search&page='
    end_url = '&tournament_search%5Bdate_range%5D=07%2F19%2F2010+-+08%2F02%2F2019&tournament_search%5Bformat%5D=standard&tournament_search%5Bname%5D=&utf8=✓'
    df = pd.DataFrame()
    for page in range(start,stop):
        df = df.append(scrape_results_page(begin_url + str(page) + end_url))
        df.to_pickle('./StandardTourneys_In_Progress' + '.pkl')
        sleep(2)
    df.to_pickle('./StandardTourneys_full.pkl')
    return df

def get_staple_list(play_format):
    """returns format index staples for given play_format (standard, modern, legacy, etc.)"""
    with requests.get('https://www.mtggoldfish.com/index/'+play_format) as r:
        soup = BeautifulSoup(r.text,'html.parser')
        card_names = []
        td_cards = soup.find_all(lambda tag: tag.name == "td" and tag.get('class') == ['card'])
        for card in td_cards:
            card_names.append(card.text)
        
        cards_no_repeats = list(set(card_names))
        return cards_no_repeats