# Magic the Gathering Price Predictor
## Summary:
The purpose of this notebook is to output price predictions for modern staples as determined by a pretrained LSTM RNN. This neural network is trained on historical price and tournament play data, using a 30 day lag time and makes predictions for 7 days into the future. There are over 300 cards in the dataset and there are options for keeping the dataset up to date in this notebook. All of the tournament and price data are scraped from MTGGoldfish. 

## About the dataset
All of the price and tournament play data were webscraped from MTGGoldfish.com. There are over 300 cards in the dataset and there are options for keeping the dataset up to date in this notebook.

AllTourneys.json contains every modern tournament decklist up to date. Each entry contains the tournament Date, a unique tournament id_num and a list of decklists reported for that tournament (usually a top-16 or all 5-0 decks for online tournaments).

Copies_Played_Culled.csv has reduced the data from AllTourneys.json to card counts for each tournament in the dataset. There are 342 columns, one for each card and an additional column for the total number of cards played in decks for that tournament (for normalization).

All_Prices.csv contains historical pricing data for the cards in the dataset. Some price histories go as far back as 2011, but many of the cards are not even that old.

The files DataIngestion.py and MTGDeckScraper.py contain useful functions for scraping new data from mtggoldfish and keeping these files up to date automatically.

Finally, SetList.json and AllCards.json are files downloaded from MTGJSON for determining printings and other card characteristics during the scraping process. These files can be kept up to date by downloading the latest versions from their website periodically (they should remain up to date for months)
