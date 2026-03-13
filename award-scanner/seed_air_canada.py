from crawler.air_canada import search_air_canada
from db.database import upsert_awards

awards = search_air_canada('YTO', 'NYC', '2026-03-31')
print('AC awards trovati:', len(awards))
print(awards)
upsert_awards(awards)
print('Salvati nel DB!')
