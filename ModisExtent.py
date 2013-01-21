from geoalchemy import GeometryColumn
from geoalchemy import GeometryDDL
from geoalchemy import Polygon
from shapely.wkb import loads
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ModisExtent(Base):
    __tablename__ = 'modis_extent'

    gid = Column(Integer, primary_key=True)
    geometry = GeometryColumn(Polygon(2))
    tile = Column(String)
    subtile = Column(String)

    def __repr__(self):
        return "<ModisExtent('%s','%s', '%s', '%s')>"\
            % (self.gid, loads(str(self.geometry.geom_wkb)).wkt, self.tile, self.subtile)

GeometryDDL(ModisExtent.__table__)