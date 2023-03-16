
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, CHAR, Date, DateTime,\
    UniqueConstraint, ForeignKeyConstraint, Column,\
    ForeignKey, Unicode, Float,\
    create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

class ImageTag(Base):
    __tablename__ = "ImageTags"
    imageid = Column(ForeignKey("Images.id"), primary_key=True)
    tagid = Column(ForeignKey("Tags.id"), primary_key=True)

    image = relationship("Image", backref="tag_assoc")
    tag = relationship("Tag", backref="img_assoc")

class Image(Base):
    __tablename__ = "Images"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    tags = relationship("Tag", secondary="ImageTags")

class Tag(Base):
    __tablename__ = "Tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    images = relationship("Image", secondary="ImageTags")


"""
class ImageTag(Base):
    __tablename__ = 'ImageTags'

    imageid = Column(Integer, ForeignKey('Images.id'), primary_key=True)
    tagid = Column(Integer, ForeignKey('Tags.id'), primary_key=True)

    image = relationship("Image", backref="parent_associations")
    tag = relationship("Tag", backref="child_associations")

class Image(Base):
    __tablename__ = 'Images'
    id = Column(Integer, primary_key=True)
    name = Column(String(10))

class Tag(Base):
    __tablename__ = 'Tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(10))
    images = relationship("Image", secondary="ImageTags")

"""

engine = create_engine("sqlite:///ass.db")

Base.metadata.create_all(engine)

Session = sessionmaker(engine)
db = Session()
t = Tag(name="TagName")
i = Image(name="ImageName")

t.images.append(i)

db.add(t)
db.commit()
db.close()
