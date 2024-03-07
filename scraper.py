from concurrent.futures import ThreadPoolExecutor
from lxml import html
import requests, csv, os


headers = {
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Referer': 'https://ustoy.com/',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
    }

def product_lists():
    product_links = []
    counter = 1
    while counter <= 60:
        url = f"https://ustoy.com/catalog/seo_sitemap/product/?p={counter}"
        response = requests.get(url, headers=headers)
        parsed_html = html.fromstring(response.content)
        sitemap_links = parsed_html.xpath("//ul[@class='sitemap']/li/a")

        print(f"Getting product links from page {counter}: {len(sitemap_links)} products found")

        for sitemap in sitemap_links:
            product_link = sitemap.get('href')
            if product_link not in product_links:
                product_links.append(product_link)

        counter += 1

    return product_links


def product_scrape(product_links):
    print(f"Scraping {product_links}")

    parsed_products = []
    try:
        response = requests.get(product_links, headers=headers)
        if response.status_code == 200:
            parsed_html = html.fromstring(response.content)

            title_element = parsed_html.xpath("//meta[@property='og:title' and @content]")
            title = title_element[0].get('content')

            product_url = product_links

            image_element = parsed_html.xpath("//img[@class='gallery-image visible' and @src]")
            image = ''
            if image_element:
                image = "https:" + image_element[0].get('src')

            sku_element = parsed_html.xpath("//meta[@property='product:retailer_item_id' and @content]")
            sku = ''
            if sku_element:
                sku = sku_element[0].get('content')

            price_element = parsed_html.xpath("//meta[@property='product:price:amount' and @content]")
            price = ''
            if price_element:
                price = price_element[0].get('content')

            availability_element = parsed_html.xpath("//meta[@property='product:availability' and @content]")
            availability = ''
            if availability_element:
                availability = availability_element[0].get('content')
            
            stock_element = parsed_html.xpath("//p[@class='availability-only']/span")
            stock = ''
            if stock_element:
                stock = stock_element[0].get('title')

            product_info = {
                "Title": title,
                "Product URL": product_url,
                "Image URL": image,
                "SKU": sku,
                "Availability": availability,
                "Stock": stock,
                "Price": "$" + str(price),
            }

            parsed_products.append(product_info)
        
    except requests.exceptions.RequestException as e:
        print(e, product_links)
         
    return parsed_products


def write_products(parsed_products):
    if not parsed_products:
        print("No product found")
        return
        
    with open('ustoy.com.csv', 'a', encoding = 'utf-8', newline = '') as f:
        fieldnames = ["Title", "Product URL", "Image URL", "SKU", "Availability", "Stock", "Price"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if f.tell() == 0:
            writer.writeheader()

        for product in parsed_products:
            writer.writerow(product)
        
        f.flush


def scrape_and_write(product_url):
    scraped_products = product_scrape(product_url)
    write_products(scraped_products)


def main():
    try:
        
        listing = product_lists()
        
        current_directory = os.path.dirname(os.path.realpath(__file__))
        relative_file_path = "\\ustoy.com.csv"
        csv_file_path = current_directory + relative_file_path

        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(scrape_and_write, url) for url in listing]
            for future in futures:
                try:
                    future.result()
                except KeyboardInterrupt:
                    print("Interrupted by the user, exiting ...")
                    executor.shutdown(wait=False)
                    os._exit(0)
    except Exception as e:
        print(f"An error occured: {e}")
        os._exit(1)


if __name__ == '__main__':
    main()