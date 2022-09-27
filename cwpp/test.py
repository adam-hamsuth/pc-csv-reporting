from pcpi import session_loader
from loguru import logger

session_man = session_loader.onprem_load_from_file(logger=logger)

session = session_man.create_cwp_session()


res = session.request('GET', '/api/v22.06/images', params={'fields':'labels', 'compact':'false'})

for blob in res.json():

    print(blob)
    print()

