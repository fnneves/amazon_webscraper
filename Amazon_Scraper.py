import requests
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from time import sleep

# http://www.networkinghowtos.com/howto/common-user-agent-list/
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})


def search_product_list(interval_count = 1, interval_hours = 6):
    """
    This function lods a csv file named TRACKER_PRODUCTS.csv, with headers: [url, code, buy_below]
    It looks for the file under in ./trackers
    
    It also requires a file called SEARCH_HISTORY.xslx under the folder ./search_history to start saving the results.
    An empty file can be used on the first time using the script.
    
    Both the old and the new results are then saved in a new file named SEARCH_HISTORY_{datetime}.xlsx
    This is the file the script will use to get the history next time it runs.

    Parameters
    ----------
    interval_count : TYPE, optional
        DESCRIPTION. The default is 1. The number of iterations you want the script to run a search on the full list.
    interval_hours : TYPE, optional
        DESCRIPTION. The default is 6.

    Returns
    -------
    New .xlsx file with previous search history and results from current search

    """
    prod_tracker = pd.read_csv('trackers/TRACKER_PRODUCTS.csv', sep=';')
    prod_tracker_URLS = prod_tracker.url
    tracker_log = pd.DataFrame()
    now = datetime.now().strftime('%Y-%m-%d %Hh%Mm')
    interval = 0 # counter reset
    
    while interval < interval_count:

        for x, url in enumerate(prod_tracker_URLS):
            page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(page.content, features="lxml")
            
            #product title
            title = soup.find(id='productTitle').get_text().strip()
            
            # to prevent script from crashing when there isn't a price for the product
            try:
                price = float(soup.find(id='priceblock_ourprice').get_text().replace('.', '').replace('€', '').replace(',', '.').strip())
            except:
                # this part gets the price in dollars from amazon.com store
                try:
                    price = float(soup.find(id='priceblock_saleprice').get_text().replace('$', '').replace(',', '').strip())
                except:
                    price = ''

            try:
                review_score = float(soup.select('i[class*="a-icon a-icon-star a-star-"]')[0].get_text().split(' ')[0].replace(",", "."))
                review_count = int(soup.select('#acrCustomerReviewText')[0].get_text().split(' ')[0].replace(".", ""))
            except:
                # sometimes review_score is in a different position... had to add this alternative with another try statement
                try:
                    review_score = float(soup.select('i[class*="a-icon a-icon-star a-star-"]')[1].get_text().split(' ')[0].replace(",", "."))
                    review_count = int(soup.select('#acrCustomerReviewText')[0].get_text().split(' ')[0].replace(".", ""))
                except:
                    review_score = ''
                    review_count = ''
            
            # checking if there is "Out of stock"
            try:
                soup.select('#availability .a-color-state')[0].get_text().strip()
                stock = 'Out of Stock'
            except:
                # checking if there is "Out of stock" on a second possible position
                try:
                    soup.select('#availability .a-color-price')[0].get_text().strip()
                    stock = 'Out of Stock'
                except:
                    # if there is any error in the previous try statements, it means the product is available
                    stock = 'Available'

            log = pd.DataFrame({'date': now.replace('h',':').replace('m',''),
                                'code': prod_tracker.code[x], # this code comes from the TRACKER_PRODUCTS file
                                'url': url,
                                'title': title,
                                'buy_below': prod_tracker.buy_below[x], # this price comes from the TRACKER_PRODUCTS file
                                'price': price,
                                'stock': stock,
                                'review_score': review_score,
                                'review_count': review_count}, index=[x])

            try:
                # This is where you can integrate an email alert!
                if price < prod_tracker.buy_below[x]:
                    print('************************ ALERT! Buy the '+prod_tracker.code[x]+' ************************')
            
            except:
                # sometimes we don't get any price, so there will be an error in the if condition above
                pass

            tracker_log = tracker_log.append(log)
            print('appended '+ prod_tracker.code[x] +'\n' + title + '\n\n')            
            sleep(5)
        
        interval += 1# counter update
        
        sleep(interval_hours*1*1)
        print('end of interval '+ str(interval))
    
    # after the run, checks last search history record, and appends this run results to it, saving a new file
    last_search = glob('./search_history/*.xlsx')[-1] # path to file in the folder
    search_hist = pd.read_excel(last_search)
    final_df = search_hist.append(tracker_log, sort=False)
    
    final_df.to_excel('search_history/SEARCH_HISTORY_{}.xlsx'.format(now), index=False)
    print('end of search')

search_product_list()
