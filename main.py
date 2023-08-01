import requests
from bs4 import BeautifulSoup
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import webbrowser
import re
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', 200)


def scrape_page(url):
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using Beautiful Soup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all <span> elements with class="title px18"
        elements = soup.find_all('span', class_='title px18')
        elements_price = soup.find_all('span', class_='price')
        ul_tags_list = soup.find_all('ul', class_='tags hide-on-small-only')

        titles = []
        prices = []
        prices_eu = []
        prices_kn = []
        tags_info_list = []
        for element, price, ul_tags in zip(elements, elements_price, ul_tags_list):
            # Find all <li> elements within the <ul> element
            li_elements = ul_tags.find_all('li')

            # Extract and store the tags data in a dictionary
            tags_info = {}
            for li in li_elements:
                tag_text = li.get_text().strip()
                tag_key, _, tag_value = tag_text.partition(':')
                tags_info[tag_key.strip()] = tag_value.strip()

            # Extract and store the data in lists
            title = element.get_text().strip()
            price = price.get_text().strip()
            price_eur = price.split(' ~')[0]
            price_eur = int(re.sub(r'[^\d]', '', price_eur))
            price_kn = price.split('~')[1]
            price_kn = int(re.sub(r'[^\d]', '', price_kn))
            titles.append(title)
            prices.append(price)
            prices_eu.append(price_eur)
            prices_kn.append(price_kn)
            tags_info_list.append(tags_info)

        # Create a DataFrame from the collected data
        data = {
            'Title': titles,
            'Price': prices,
            'Price EU': prices_eu,
            'Price KN': prices_kn,
            'Tags': tags_info_list
        }
        df = pd.DataFrame(data)

        return df
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")


def generate_report(df):
    template_str = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Web Report</title>
        <style>
            table {
                font-family: Arial, sans-serif;
                border-collapse: collapse;
                width: 100%;
            }

            th {
                background-color: #f2f2f2;
            }

            th, td {
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }
        </style>
    </head>
    <body>
        <h1>Web Report</h1>
        <table>
            <tr>
                <th>Title</th>
                <th>Price</th>
                <th>Price EUR</th>
                <th>Price KN</th>
                <th>Tags</th>
            </tr>
            {% for index, row in df.iterrows() %}
            <tr>
                <td width='70%'>{{ row['Title'] }}</td>
                <td>{{ row['Price'] }}</td>
                <td>{{ row['Price EU'] }}</td>
                <td>{{ row['Price KN'] }}</td>
                <td>
                    <ul>
                    {% for key, value in row['Tags'].items() %}
                        <li>{{ key }}: {{ value }}</li>
                    {% endfor %}
                    </ul>
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''

    env = Environment(loader=FileSystemLoader('.'))
    template = env.from_string(template_str)
    report_html = template.render(df=df)

    with open('report.html', 'w', encoding='utf-8') as file:  # Specify encoding='utf-8'
        file.write(report_html)

def main():
    base_url = 'https://www.index.hr/oglasi/osobni-automobili/gid/27?pojamZup=-2&markavozila=11944&modelvozila=11969&tipoglasa=1&sortby=2&elementsNum=100&grad=0&naselje=0&cijenaod=0&cijenado=40450&vezani_na=179-1190_470-910_1172-1335_359-1192&num='

    num_pages = 7  # Set the number of pages you want to scrape

    all_data = []  # To store DataFrames from each page

    for page in range(1, num_pages + 1):
        page_url = f"{base_url}{page}"
        print(f"Scraping page {page} - URL: {page_url}")
        data_page = scrape_page(page_url)
        if data_page is not None:
            all_data.append(data_page)

    # Concatenate all DataFrames from each page into a single DataFrame
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        print("\nDataFrame containing all scraped data:")
        print(df_all.head(len(df_all)))

        # Generate the offline report
        generate_report(df_all)
    else:
        print("No data found.")


if __name__ == "__main__":
    main()
    webbrowser.open('report.html')
