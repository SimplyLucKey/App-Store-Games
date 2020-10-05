from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import csv
import io


class app_store_scraper:

    def __init__(self):
        self.PATH = 'C:\Program Files (x86)\chromedriver.exe'
        self.t0 = time.time()

    # recrusive function
    def get_all_apps(self, letter, bookmark_url=None):

        # chrome driver
        driver = webdriver.Chrome(self.PATH)
        debug_url = None

        # comment/uncomment if there is a problem
        # debug_url = 'https://apps.apple.com/us/genre/ios-games/id6014?letter=Z&page=10#page'


        # load up app store
        if bookmark_url:
            driver.get(bookmark_url)

        elif debug_url:
            driver.get(debug_url)

        else:
            url = f'https://apps.apple.com/us/genre/ios-games/id6014?letter={letter}'
            driver.get(url)

        expected_wait = WebDriverWait(driver, 30, ignored_exceptions=(NoSuchElementException,
                                                        StaleElementReferenceException,
                                                        ElementNotInteractableException))


        # app dictionary
        app_dict = {}


        # failsafe if not on app page
        try:

            # new bookmark url everytime it runs
            bookmark_url = driver.current_url

            # app column
            app_col = expected_wait.until(EC.presence_of_element_located((By.ID, 'selectedcontent')))


            # get app name
            app_name = app_col.text.split('\n')


            # scrap data for app_info
            for app in app_name:

                # form a dictionary
                app_info = {'link': None, 'rating': None, 'rating_count': None, 'subtitles': None, 'description': None,
                            'company': None, 'size': None, 'language': None, 'age_rating': None, 'price': None,
                            'latest_version_date': None, 'icon': None, 'in-app_purchase': None, 'category': None}

                app_dict[app] = app_info


                # go into each app page
                # failsafe while in app page
                try:
                    app_page = expected_wait.until(EC.element_to_be_clickable((By.LINK_TEXT, app)))
                    app_page.click()

                except ElementNotInteractableException:
                    driver.execute_script('window.scrollTo(0, document.body.scrollHeight / 3)')
                    app_page = expected_wait.until(EC.element_to_be_clickable((By.LINK_TEXT, app)))
                    app_page.click()


                # page source for bs4
                driver.implicitly_wait(10)
                pg_source = driver.page_source
                soup = BeautifulSoup(pg_source, features='html.parser')
                try:
                    '''
                    table1: for subtitles, rating, and rating count
                    table2: for description
                    table3: for information section
                    table4: for company
                    '''
                    table1 = soup.find('div', class_='l-column small-7 medium-8 large-9 small-valign-top')
                    table2 = soup.find('div', class_='section__description')
                    table3 = soup.find('dl', class_=re.compile('information-list information-list--app.*'))
                    table4 = soup.find('h2', class_=re.compile('product-header__identity.*'))


                    # scraping data
                    # app page link
                    app_dict[app]['link'] = soup.find('meta', property='og:url')['content']


                    # rating & rating count
                    try:
                        ratings = table1.find('figcaption', class_='we-rating-count star-rating__count').text.split('•')
                        app_dict[app]['rating'] = ratings[0]
                        app_dict[app]['rating_count'] = re.sub(r'\sRating.*', '', ratings[1].strip())

                    except:
                        pass


                    # subtitles
                    try:
                        app_dict[app]['subtitles'] = table1.find('h2',
                                                                 class_='product-header__subtitle app-header__subtitle').text
                    except:
                        pass


                    # description
                    app_dict[app]['description'] = table2.find(class_=re.compile('we-truncate.*')).text.lstrip()



                    # company
                    app_dict[app]['company'] = table4.find(class_='link').text.lstrip().rstrip()


                    # size, language, age_rating, price, in-app purchase
                    information = table3.find_all('dt')
                    for info in information:

                        if info.text == 'Size':
                            app_dict[app]['size'] = info.find_next_sibling().text.lstrip().rstrip()

                        elif info.text == 'Category':
                            app_dict[app]['category'] = info.find_next_sibling().text.lstrip().rstrip()

                        elif info.text == 'Languages':
                            app_dict[app]['language'] = info.find_next_sibling().text.lstrip().rstrip()

                        elif info.text == 'Age Rating':
                            app_dict[app]['age_rating'] = info.find_next_sibling().text.lstrip().rstrip()

                        elif info.text == 'Price':
                            app_dict[app]['price'] = info.find_next_sibling().text.lstrip().rstrip()

                        elif info.text == 'In-App Purchases':
                            app_dict[app]['in-app_purchase'] = 'Yes'


                    # latest version date
                    try:
                        app_dict[app]['latest_version_date'] = soup.find(attrs={'data-test-we-datetime': True}).text

                    except:
                        pass


                    # icon
                    icon_pic = soup.find('picture', class_=re.compile('we-artwork ember-view.*'))
                    app_dict[app]['icon'] = icon_pic.find('source')['srcset'].split()[0]

                    driver.back()


                except:
                    with open('app_error_list.csv', 'a', newline='') as f:

                        # write to list
                        writer = csv.writer(f)
                        writer.writerow([app, bookmark_url, app_dict[app]['link']])

                    app_dict.popitem()
                    driver.back()
                    continue


        # remove blank entry for an error scenario
        # save error list
        except:
            with open('error_list.csv', 'a', newline='') as f:

                # write to list
                writer = csv.writer(f)
                writer.writerow([app, bookmark_url])

            app_dict.popitem()
            driver.back()


        # save everything in the dict
        finally:

            # the next button
            try:
                next_btn = expected_wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'paginate-more')))
                if next_btn:
                    bookmark_url = next_btn.get_attribute('href')
                next_pg = True

            except:
                next_pg = False


            driver.close()
            driver.quit()


            # input character different than url character
            if letter == '*':
                csv_name = 'appstore_games_#.csv'

            else:
                csv_name = f'appstore_games_{letter}.csv'


            # save to csv
            with io.open(csv_name, 'a', newline='', encoding='utf-8') as f:

                # same headers
                fieldnames = ['apps', 'link', 'rating', 'rating_count', 'subtitles', 'description',
                              'company', 'size', 'language', 'age_rating', 'price',
                              'latest_version', 'icon', 'in-app_purchase', 'category']

                # write from dictionary
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                for app, info in app_dict.items():
                    writer.writerow({'apps': app, 'link': info['link'], 'rating': info['rating'],
                                     'rating_count': info['rating_count'], 'subtitles': info['subtitles'],
                                     'description': info['description'], 'company': info['company'],
                                     'size': info['size'], 'language': info['language'],
                                     'age_rating': info['age_rating'], 'price': info['price'],
                                     'latest_version': info['latest_version_date'], 'icon': info['icon'],
                                     'in-app_purchase': info['in-app_purchase'], 'category': info['category']})

            # print(round(time.time() - self.t0, 3))
            return bookmark_url, next_pg

if __name__ == '__main__':
    app_store_scraper()