import datetime
import collections
import re
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, CHAR, Date, DateTime,\
    UniqueConstraint, ForeignKeyConstraint, Column,\
    ForeignKey, Unicode, Float, Binary, DATETIME,\
    create_engine
from sqlalchemy.orm import relationship, sessionmaker, backref
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

class ISODateTime(TypeDecorator):
    impl = String

    def process_result_value(self, value, dialect):
        if not isinstance(value, (str, unicode)):
            return None
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

    def process_bind_param(self, value, dialect):
        return datetime.isoformat(value)

class AlbumRoot(Base):
    __tablename__ = "AlbumRoots"
    id            = Column(Integer, primary_key=True)
    label         = Column(String(100))
    status        = Column(Integer)
    type          = Column(Integer)
    identifier    = Column(String(300))
    directory     = Column("specificPath", String(1000))
    ux = UniqueConstraint(identifier, directory)
    albums = relationship("Album", back_populates="root")

    @property
    def path(self):
        re_path = re.compile(r"^volumeid:\?path=(.*)$")
        ma = re_path.match(self.identifier)
        if ma:
            return ma.group(1) + self.directory
        else:
            raise RuntimeError("Can't decode %s from AlbumRoot %d" %\
                (self.identifier, self.id))

class Album(Base):
    __tablename__ = "Albums"
    id            = Column(Integer, primary_key=True)
    root_id       = Column("AlbumRoot", ForeignKey('AlbumRoots.id'))
    directory     = Column("relativePath", String(1000))
    date          = Column(Date)
    caption       = Column(Unicode(10000))
    collection    = Column(String(100))
    icon          = Column(Integer)
    root = relationship("AlbumRoot", back_populates="albums")
    images = relationship("Image", back_populates="album")
    ux = UniqueConstraint(root_id, directory)

    @property
    def path(self):
        return self.root.path + self.directory

class ImageTag(Base):
    __tablename__ = "ImageTags"
    imageid    = Column(ForeignKey("Images.id"), primary_key=True)
    tagid      = Column(ForeignKey("Tags.id"), primary_key=True)
#    image      = relationship("Image")
#    tag        = relationship("Tag")

class Image(Base):
    __tablename__ = "Images"
    id         = Column(Integer, primary_key=True)
    album_id   = Column("album", ForeignKey("Albums.id"))
    name       = Column(String(200))
    status     = Column(Integer)
    category   = Column(Integer)
    mtime      = Column("modificationDate", ISODateTime)
    size       = Column("fileSize", Integer)
    hash       = Column("uniqueHash", CHAR(20))
    ux         = UniqueConstraint(name, album_id)
    album      = relationship("Album", back_populates="images")
    information = relationship("ImageInformation", cascade="all, delete-orphan")
    meta = relationship("ImageMetadata", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="ImageTags",
        passive_deletes="all", single_parent=True)

    @property
    def path(self):
        return os.path.join(self.album.path, self.name)

class Tag(Base):
    __tablename__ = "Tags"
    id            = Column(Integer, primary_key=True)
    pid           = Column(ForeignKey("Tags.id"))
    name          = Column(String(100))
    ux            = UniqueConstraint(pid, name)
    images        = relationship("Image", secondary="ImageTags")
    children      = relationship("Tag",
                    backref=backref("parent", remote_side=[id]),
                    cascade="all, delete-orphan")

class ImageInformation(Base):
    __tablename__ = "ImageInformation"
    id            = Column("imageid", ForeignKey("Images.id"), primary_key=True)
    rating        = Column(Integer)
    creation_date = Column("creationDate", ISODateTime)
    digit_date    = Column("digitizationDate", ISODateTime)
    width         = Column(Integer)
    height        = Column(Integer)
    orientation   = Column(Integer)
    format        = Column(String(100))
    image         = relationship("Image", back_populates="information",
                    cascade="all, delete-orphan", single_parent=True)

class ImageMetadata(Base):
    __tablename__ = "ImageMetaData"
    id              = Column("imageid", ForeignKey("Images.id"), primary_key=True)
    make            = Column("make", String(50))
    model           = Column("model", String(50))
    lens            = Column("lens", String(50))
    aperture        = Column("aperture", Float)
    focalLength     = Column("focalLength", Float)
    focalLength35   = Column("focalLength35", Float)
    exposureTime    = Column("exposureTime", Float)
    exposureProgram = Column("exposureProgram", Integer)
    exposureMode    = Column("exposureMode", Integer)
    sensitivity     = Column("sensitivity", Integer)
    flash           = Column("flash", Integer)
    whiteBalance    = Column("whiteBalance", Integer)
    whiteBalanceColorTemperature = Column("whiteBalanceColorTemperature",
        Integer)
    meteringMode    = Column("meteringMode", Integer)
    subjectDistance = Column("subjectDistance", Float)
    subjectDistanceCategory = Column("subjectDistanceCategory", Integer)
    image = relationship("Image", back_populates="meta")

class VideoMetadata(Base):
    __tablename__ = "VideoMetaData"
    id               = Column("imageid", ForeignKey("Images.id"), primary_key=True)
    aspectRatio      = Column("aspectRatio", String(10))
    audioBitRate     = Column("audioBitRate", String(10))
    audioChannelType = Column("audioChannelType", String(10))
    audioCompressor  = Column("audioCompressor", String(10))
    duration         = Column("duration", String(10))
    frameRate        = Column("frameRate", String(10))
    exposureProgram  = Column("exposureProgram", Integer)
    videoCodec       = Column("videoCodec", String(10))


class TagTree(Base):
    __tablename__ = "TagsTree"
    id         = Column(ForeignKey("Tag.id"), primary_key=True)
    pid        = Column(ForeignKey("Tag.id", primary_key=True))

class Thumbnail(Base):
    __tablename__    = "Thumbnails"
    id               = Column(Integer, primary_key=True)
    type             = Column(Integer)
    date             = Column("modificationDate", String(100))
    orientation      = Column("orientationHint", Integer)
    data             = Column(Binary)
    file_path = relationship("FilePath", back_populates="thumbnail",
        uselist=False)

class FilePath(Base):
    __tablename__    = "FilePaths"
    path             = Column(String(1000), primary_key=True)
    thumb_id         = Column("thumbId", ForeignKey("Thumbnails.id"))
    thumbnail = relationship("Thumbnail", back_populates="file_path")

def scan_files(basedir):
    f_dict = collections.defaultdict(list)
    for root, dirs, files in os.walk(basedir):
        for f in files:
            f_dict[f].append(root)
    return f_dict

def check_db(db):
    i = 0
    basedir = "/media/mobile/Bilder"
    files = scan_files(basedir)
    for img in db.query(Image):
        if img.album:
            path = img.path
        else:
            path = None
        if not img.album or not path:
            print("DELETE", img.id, [t.name for t in img.tags])
            db.delete(img)
        i += 1
        if i % 1000 == 0:
            print(i)
    db.commit()

def check_tn(db):
    for tn in db.query(Thumbnail).join(FilePath):
        path = tn.file_path.path
        if not path.startswith("/media/mobile/Bilder"):
            db.delete(tn)
            print(path)
    db.commit()

if __name__ == "__main__":

    engine = create_engine("sqlite://")
    engine.execute("ATTACH DATABASE '/media/mobile/Bilder/digikam4.db' AS miiin")
    engine.execute("ATTACH DATABASE '/media/mobile/Bilder/thumbnails-digikam.db' AS thumbnails")
#    engine = create_engine("sqlite:////media/mobile/Bilder/digikam4.db")
    Session = sessionmaker(engine)
    db = Session()

