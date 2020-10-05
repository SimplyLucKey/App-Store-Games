from app_store_scraper import app_store_scraper
import string

alphabet_list = list(string.ascii_uppercase)
alphabet_list.append('*')


if __name__ == '__main__':

    # loop through all alphabets
    scraper = app_store_scraper()
    for alphabet in alphabet_list:
        bookmark_url, next_pg = scraper.get_all_apps(alphabet)

        while next_pg:
            bookmark_url, next_pg = scraper.get_all_apps(alphabet, bookmark_url)
