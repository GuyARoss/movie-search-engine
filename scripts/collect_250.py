import requests
from bs4 import BeautifulSoup
import csv

url = 'https://www.imdb.com/chart/top/'

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find('tbody', {'class': 'lister-list'})

movies = []

for row in table.find_all('tr'):
    cover_url = row.find('td', {'class': 'posterColumn'}).a.img['src']
    title = row.find('td', {'class': 'titleColumn'}).a.text.strip()
    year = row.find('td', {'class': 'titleColumn'}).span.text.strip('()')
    rating = row.find('td', {'class': 'ratingColumn imdbRating'}).strong.text.strip()
    movies.append([title, year, rating, cover_url])

with open('top250.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Title', 'Year', 'IMDb Rating', 'Cover URL'])
    writer.writerows(movies)