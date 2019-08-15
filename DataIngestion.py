#Run this cell for scraping the latest page of tournaments (This takes a while)
import pandas as pd
import MTGDeckScraper
from time import sleep

def f_d(num):
    return("{:02d}".format(num))

def Update_Tourneys(manual_break = 5):
    All_Tourneys = pd.read_json('All_Tourneys.json')
    All_Tourneys = All_Tourneys.sort_values(by='Date')

    today = pd.to_datetime('today')
    last_day = All_Tourneys.iloc[-1]['Date']
    last_id = All_Tourneys.iloc[-1]['id_num']

    end_date = '+-+' + f_d(today.month) + '%2F' + f_d(today.day) + '%2F'+ f_d(today.year)
    start_date = f_d(last_day.month) + '%2F' + f_d(last_day.day) + '%2F'+ f_d(last_day.year)
    date_range = start_date + end_date
    str1 = 'https://www.mtggoldfish.com/tournament_searches/create?commit=Search&page='
    str2 = '&tournament_search%5Bdate_range%5D='
    str3 = '&tournament_search%5Bformat%5D=modern&tournament_search%5Bname%5D=&utf8=%E2%9C%93'

    page = 1
    stop = False
    df = pd.DataFrame()
    while stop == False:
        df = df.append(MTGDeckScraper.scrape_results_page(str1 +str(page) + str2 + date_range + str3))
        df_id_num = pd.to_numeric(df.id_num)
        if (last_id in df.id_num.values) or (page > manual_break):
            stop = True
        page+=1
        sleep(2)

    #To json    
    All_Tourneys = All_Tourneys.append(df)
    All_Tourneys = All_Tourneys.drop_duplicates(subset='id_num')
    All_Tourneys = All_Tourneys.sort_values(by='Date')
    All_Tourneys = All_Tourneys.reset_index().drop('index',axis=1)
    All_Tourneys.to_json('All_Tourneys.json')
    
    Copies = pd.read_csv('Copies_Played_Culled.csv')

    All_Tourneys = pd.read_json('All_Tourneys.json')
    All_Tourneys = All_Tourneys.sort_values(by='Date')
    All_Tourneys = All_Tourneys.drop_duplicates(subset='id_num')

    Card_List = Copies.keys()[4:]
    if Card_List[0] != 'Hazoret the Fervent':
        raise ValueError('Card_List is Invalid.')

    All_Tourneys['Total'] = All_Tourneys.Decks.apply(lambda z: sum([sum([x[1] for x in y]) for y in z]))
    for card in Card_List:
        #Creates column of total copies of that card played in each tournament
        All_Tourneys[card] = All_Tourneys.Decks.apply(lambda z: sum([sum([x[1] for x in y if x[0] == card]) for y in z]))
        print(card+'...Done')

    All_Tourneys = All_Tourneys.drop('Decks', axis = 1)
    All_Tourneys = All_Tourneys.drop_duplicates(subset='id_num')
    All_Tourneys.to_csv('Copies_Played_Culled.csv')

def UpdatePrices():    
    #Run this cell to update price data
    Prices = pd.read_csv('All_Prices.csv')

    AllCards = pd.read_json('AllCards.json')
    SetList = pd.read_json('SetList.json')
    SetList.releaseDate = pd.to_datetime(SetList.releaseDate)

    Card_list = Prices.keys()[1:]
    print(Card_list[0])
    if Card_list[0] != 'Hazoret the Fervent':
        raise ValueError('Card_List is Invalid.')

    AllPrices = pd.DataFrame()
    for card in Card_list:
        #Find earliest printing in an expansion
        card_printings = SetList[SetList['code'].isin(AllCards[card]['printings'])]
        card_printings = card_printings[(card_printings.type == 'expansion') | (card_printings.type == 'core')]
        if len(card_printings) > 0:
            set_name = card_printings[card_printings.releaseDate == card_printings.releaseDate.min()].name.values[0]
            if set_name == 'Magic 2014':
                set_name = 'Magic 2014 Core Set'
            if set_name == 'Magic 2015':
                set_name = 'Magic 2015 Core Set'
            print('Getting: ' + set_name + ' '+ card)
            Price = MTGDeckScraper.get_price_history(set_name, card)
            Price = Price.set_index(Price.Date)
            Price[card] = Price.Price
            AllPrices = pd.concat([AllPrices,Price[card]], join = 'outer', axis = 1)
            sleep(1)
    AllPrices.to_csv('All_Prices.csv')