from geoalchemy import GeometryColumn
from geoalchemy import GeometryDDL
from geoalchemy import Polygon
from shapely.wkb import loads
from sqlalchemy.schema import Column
from sqlalchemy.types import Boolean
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ModisExtent(Base):
    __tablename__ = 'modis_extent'

    pk = Column(Integer, primary_key=True)
    name = Column(String)
    geometry = GeometryColumn("geom", Polygon(2))
    h = Column(Integer)
    v = Column(Integer)
    available = Column(Boolean)

    def __repr__(self):
        return "<ModisExtent('%s','%s', '%s')>"\
            % (self.pk, loads(str(self.geometry.geom_wkb)).wkt, self.name)

GeometryDDL(ModisExtent.__table__)
