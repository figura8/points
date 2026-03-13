from crawler.united import search_united
from db.database import upsert_awards

awards = search_united('EWR', 'LAX', '2026-04-15')
print('Awards trovati:', len(awards))
print(awards)
upsert_awards(awards)
print('Salvati nel DB!')
