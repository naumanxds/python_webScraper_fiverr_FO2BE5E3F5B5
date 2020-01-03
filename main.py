import csv

from datetime import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from urllib.parse import  urljoin

# constants used in code
NOT_FOUND = 'None'
BASE_URL = 'https://shop.lrworld.com'

# create browser instance
manager = GeckoDriverManager()
browserOptions = Options()
browserOptions.add_argument("--headless")
driver = webdriver.Firefox(executable_path=manager.install(), options=browserOptions)

# create topseller file and error file
fError = open('ERROR_LOGS.log', 'a', encoding="utf-8")
fTopSeller = open('TopSeller-' + datetime.now().strftime('%d-%b-%y_%T') + '.csv', 'w', encoding="utf-8")

def logError(error, url):
    fError.write('======> ERROR (' + datetime.now().strftime('%d-%b-%y %T') + ') <====== \n\n')
    fError.write('       >> URL >> ' + url)
    fError.write('\n       >> Error >> ' + error)
    fError.write('\n\n======> ERROR END <======\n')

# get html of the provided page url
def getHtml(url):
    try:
        driver.get(url)
        driver.execute_script('return document.documentElement.outerHTML')
        return BeautifulSoup(driver.page_source, 'lxml')

    except Exception as e:
        logError('Error in Fetching HTML == ' + format(e), url)

    return False

# write in file
def writeFile(fHandle, data, url = ''):
    try:
        csvWriter = csv.writer(fHandle)
        csvWriter.writerow(data)
    except Exception as e:
        logError('Error in Writing Data into the file == ' + format(e), url)

# iterate through the fetched links get data and place in the file
def iterateLinks(links, fHandle):
    for link in links:
        try:
            # create proper link for product listing page
            url = urljoin(BASE_URL, link.find('a').get('href'))

            # get product listing page and find products
            productListing = getHtml(url)
            products = productListing.find('ul', {'class' : 'product-list'})

            # check if products exist else continue
            if str(products) == NOT_FOUND:
                logError('No Product Listing found', url)
                continue

            for product in products.find_all('li'):
                # error check set to False before scraping of each product
                error = False

                productLink = product.find('a').get('href')
                productDetail = getHtml(productLink)

                div = productDetail.find('div', {'class' : 'product-description-name'})
                if str(div) != NOT_FOUND:
                    title = div.find('h1')
                    if str(title) != NOT_FOUND:
                        title = title.get_text(strip=True)
                    else:
                        error = True
                        logError('Title Not Found', productLink)
                else:
                    error = True
                    logError('Title Not Found', productLink)


                productNo = div.find('p')
                if str(productNo) != NOT_FOUND:
                    productNo = productNo.get_text(strip=True).split('Artikelnummer: ')[1]
                else:
                    error = True
                    logError('Product Number not Found', productLink)

                div = productDetail.find('div', {'class' : 'product-description-list'})
                if str(div) != NOT_FOUND:
                    shortDesc = div.find('ul')
                    if str(shortDesc) != NOT_FOUND:
                        shortDesc = shortDesc.get_text(strip=True, separator='\n')
                    else:
                        error = True
                        logError('Short Description not Found', productLink)
                else:
                    error = True
                    logError('Short Description not Found', productLink)


                div = productDetail.find('div', {'class' : 'product-price'})
                if str(div) != NOT_FOUND:
                    price = div.find('div', {'class' : 'price'})
                    if str(price) == NOT_FOUND:
                        price = div.find('div', {'class' : 'price special'})

                    if str(price) != NOT_FOUND:
                        price = price.get_text(strip=True)
                    else:
                        price = 'Price Not Found'


                div = productDetail.find('div', {'class' : 'content active'})
                if str(div) != NOT_FOUND and str(div.find_all('p')) != NOT_FOUND:
                    description = div.find_all('p')
                    descriptionTxt = ''
                    for desc in description:
                        descriptionTxt += desc.get_text(strip=True, separator='\n') + '\n'
                else:
                    error = True
                    logError('Description Not Found', productLink)

                writeFile(fHandle, [title, productNo, shortDesc, price, descriptionTxt], productLink)

                # check if product is topseller
                if str(product.find('span', {'class' : 'eyecatcher topseller'})) == NOT_FOUND:
                    writeFile(fTopSeller, [title, productNo, shortDesc, price, descriptionTxt], productLink)

                print('         >> product done >> ' + productLink)
            print('     >> Product List Done >> ' + url)
        except Exception as e:
            logError('<< Exception >> ', format(e))

def startScraping(enteredUrl):
    print('=== Starting Scrapping ===')

    # fetch catagories
    html = getHtml(enteredUrl)
    catagories = html.find_all('section', {'class' : 'nav-content-container dl-submenu cf'})

    # iterate through all the fetched catagories
    for catagory in catagories:
        heading = catagory.find('h3').get_text(strip=True)
        links = catagory.find_all('li')

        # create file for each catagory
        fHandle = open(heading + '-csvFileCreatedAt-' + datetime.now().strftime('%d-%b-%y_%T') + '.csv', 'w', encoding="utf-8")

        # iterate throught the links for each catagory
        iterateLinks(links, fHandle)
        print(' >> catagory done >> ' + heading)
        fHandle.close()

    fTopSeller.close()
    fError.close()
    print('=== Scrapping Finished ===')


if __name__ == '__main__':
    # input for user
    enteredUrl = input('Please Enter Starting Point for Scrapper: ').rstrip('/')
    startScraping(enteredUrl)