#BeautifulSoup, requests and html.parser are all used to extract information in a readable and
#easy to parse format
from bs4 import BeautifulSoup
import requests
import html.parser
#unidecode takes unicode data and tries to represent it in ASCII characters
import unidecode
#math is needed for its ceiling function
import math
#csv is used to create a csv file that holds info for all releases found
import csv
#datetime is used to name the csv file so each csv file will be saved w/ the date in filename
import datetime

def main():
    releases = {}
    sold_out_releases = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0)'}
    #main vinyl page link split into two so that page numbers can be added in the middle:
    bb1 = "https://www.bestbuy.com/site/music/vinyl-records/pcmcat197800050048.c?cp="
    bb2 = "&id=pcmcat197800050048"
    sorts = create_sorts()
    #gather total number of vinyl records at best buy website:
    max_releases, max_pages = num_items_and_pages_per_filter(bb1, bb2, headers)
    #first run through on main vinyl page
    count = 100
    releases_first_run, sold_out_releases_first_run = run_main_vinyl_page(bb1, bb2, headers, count, releases, sold_out_releases, sorts, max_releases, count)
    final_releases, final_sold_out_releases = keep_going(releases_first_run, sold_out_releases_first_run, max_releases, headers, bb1, bb2)
    create_csvs(final_releases, final_sold_out_releases)

def create_sorts():
    sorts = []
    sorts.append("&sp=%2Bcurrentprice%20skuidsaas")
    sorts.append("&sp=-currentprice%20skuidsaas")
    sorts.append("&sp=customerrating%20numberofreviewssaas")
    sorts.append("&sp=-streetdate%20skuidsaas")
    sorts.append("&sp=%2Bskushortlabel%20skuidsaas")
    sorts.append("&sp=-skushortlabel%20skuidsaas")
    return sorts


#this function uses all of the specific sorting methods that best buy offers; it goes through each
#sort individually to add as many LPs as possible to the list. This function should ONLY be used when
#there are more than 100 pages worth of records on the default (best-selling) page. 
def run_main_vinyl_page(bb1, bb2, headers, count, releases, sold_out_releases, sorts, max_releases, items_count):
    updated_releases, updated_sold_out_releases, items_found = check_bb_page(bb1, bb2, headers, count, releases, sold_out_releases)
    total_releases = len(updated_releases) + len(updated_sold_out_releases)
    for i in range(len(sorts)):
        if (not max_releases == total_releases) or (not items_found == items_count):
                print()
                print("****sort number: " + str(sorts[i]) + "****")
                print()
                updated_releases, updated_sold_out_releases, new_items_found = check_bb_page(bb1, bb2 + sorts[i], headers, count, updated_releases, updated_sold_out_releases)
                total_releases = len(updated_releases) + len(updated_sold_out_releases)
                items_found += new_items_found
    return updated_releases, updated_sold_out_releases
    
#num refers to filter in left column of vinyl home page on bb website (up to 51, but no 42!!)
#the correct link for the filtered page will be returned
def bb_number_of_filters_by_page(headers, bb1, bb2):
    bb_vinyl_page = bb1 + "1" + bb2
    page = requests.get(bb_vinyl_page, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    num_filter_by = len(soup.find_all("a", class_="facet-seo-link"))
    return num_filter_by

#num refers to filter in left column of vinyl home page on bb website (up to 51, but no 42!!)
#the correct link for the filtered page will be returned
def bb_filter_by_page_finder(page_num, headers, bb1, bb2):
    bb_vinyl_page = bb1 + "1" + bb2
    page = requests.get(bb_vinyl_page, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    filter_by = soup.find_all("a", class_="facet-seo-link")
    filter_by_item = html.unescape(str(filter_by[page_num]))
    filter_by_item_sub = filter_by_item[filter_by_item.find('href="')+6:]
    filter_by_item_link = filter_by_item_sub[:filter_by_item_sub.find('"')]
    position_for_cp1 = filter_by_item_link.find("&id=")
    bb1 = filter_by_item_link[:position_for_cp1]+"&cp="
    bb2 = filter_by_item_link[position_for_cp1:]
    return bb1, bb2

def num_items_and_pages_per_filter(bb1, bb2, headers):
    filter_page = bb1 + "1" + bb2
    page = requests.get(filter_page, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    print("Soup: ")
    print(soup)
    print()
    soup_text = soup.find_all("div", class_="right-side")
    print("Soup text[0].text: ")
    print(soup_text[0].text)
    print()
    num_items_per_filter = int(soup_text[0].text[:soup_text[0].text.find(" items")])
    num_pages_per_filter = math.ceil(num_items_per_filter/25)
    if num_pages_per_filter > 100:
        num_pages_per_filter = 100
    return num_items_per_filter, num_pages_per_filter

def check_bb_page(bb1, bb2, headers, num_pages, releases_check, sold_out_releases_check):
    add_to_releases = releases_check
    add_to_sold_out_releases = sold_out_releases_check
    for i in range(1,num_pages):
        page = requests.get(bb1 + str(i) + bb2, headers=headers)
        soup = BeautifulSoup(page.text, 'html.parser')
        artist_sku_release_date = soup.find_all('div', class_="sku-model")
        title = soup.find_all('div', class_="sku-title")
        price = soup.find_all('div', class_="priceView-hero-price priceView-customer-price")
        in_stock = soup.find_all('div', class_="fulfillment-add-to-cart-button")
        for num in range(len(price)):
            SKU = artist_sku_release_date[num].text[(artist_sku_release_date[num].text.find("SKU:")+4):artist_sku_release_date[num].text.find(" R")]
            if SKU not in add_to_releases and SKU not in add_to_sold_out_releases:
                release_list = []
                #artist name:
                artist = artist_sku_release_date[num].text[7:artist_sku_release_date[num].text.find(" SKU")]
                release_list.append(unidecode.unidecode(artist))
                #title:
                title_of_release = title[num].text
                release_list.append(unidecode.unidecode(title_of_release))
                #release date:
                release_list.append(artist_sku_release_date[num].text[(artist_sku_release_date[num].text.find("Release Date:")+13):])
                #price:
                release_list.append(float(price[num].text[(price[num].text.find('is $')+4):]))
                #type (pre-order, in stock)
                if in_stock[num].text == "Add to Cart":
                    release_list.append("In Stock")
                else:
                    release_list.append(in_stock[num].text)
                if in_stock[num].text == "Sold Out" or in_stock[num].text== "Check Stores":
                    add_to_sold_out_releases[SKU] = release_list
                else:
                    add_to_releases[SKU] = release_list
    new_items_found = len(add_to_releases) + len(add_to_sold_out_releases) - len(releases_check) - len(sold_out_releases_check)
    return add_to_releases, add_to_sold_out_releases, new_items_found

def all_releases_found(max_releases, releases, sold_out_releases):
    all_found = False;
    total_releases = len(releases) + len(sold_out_releases)
    if max_releases == total_releases:
        all_found = True
    return all_found

def create_csvs(final_releases, final_sold_out_releases):
    releases_csv = "C:\Users\herwi\Desktop\projects\best buy record prices\releases\releases\releases-" + str(datetime.date.today()) + ".csv" 
    with open(releases_csv, "w") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["Artist", "Title", "Release Date", "Price", "Status"])
        writer.writerows(final_releases.values())
    sold_out_releases_csv = "C:\Users\herwi\Desktop\projects\best buy record prices\releases\sold out releases\sold_out_releases-" + str(datetime.date.today()) + ".csv"
    with open(sold_out_releases_csv, "w") as outfile_2:
        writer = csv.writer(outfile_2)
        writer.writerow(["Artist", "Title", "Release Date", "Price", "Status"])
        writer.writerows(final_sold_out_releases.values())

def keep_going(releases, sold_out_releases, max_releases, headers, bb1, bb2):
    current_releases = releases
    current_sold_out_releases = sold_out_releases
    total_releases = len(current_releases) + len(current_sold_out_releases)
    if not total_releases == max_releases:
        num_filters = bb_number_of_filters_by_page(headers, bb1, bb2)
        for i in range(num_filters):
            print("filter # = " + str(i))
            bb1_new, bb2_new = bb_filter_by_page_finder(i, headers, bb1, bb2)
            items_count, page_count = num_items_and_pages_per_filter(bb1_new, bb2_new, headers)
            if page_count <= 100:
                current_releases, current_sold_out_releases, new_items_found = check_bb_page(bb1_new, bb2_new, headers, page_count, current_releases, current_sold_out_releases)
            else:
                current_releases, current_sold_out_releases = run_main_vinyl_page(bb1_new, bb2_new, headers, page_count, current_releases, current_sold_out_releases, sorts, max_releases, items_count)
            total_releases = len(current_releases) + len(current_sold_out_releases)
            if total_releases == max_releases:
                i = len(num_filters)
    return current_releases, current_sold_out_releases



