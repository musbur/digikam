from models import Image, Album, AlbumRoot,\
    ImageInformation, ImageMetadata, Tag,\
    engine, Session

import pandas

db = Session()

q = db.query(Image.id, Image.mtime.label('mtime')).\
    filter(Image.mtime != None).\
    order_by(Image.mtime)

df = pandas.read_sql_query(q.statement, engine)

mytag = db.query(Tag).filter(Tag.name == 'EXPERT').first()

df['delay'] = df['mtime'].diff().apply(lambda x:x.value/int(1e9))
mindelta = 2

burst = df['delay'] < mindelta
b1 = burst.iloc[1:len(burst)].append(pandas.Series([False]))
b1.index = xrange(len(b1))
df['burst'] = burst | b1

ids = df['id'][df['burst']]

for i in ids.tolist():
    img = db.query(Image).filter(Image.id == i).first()
    img.tags.append(mytag)
db.commit()
