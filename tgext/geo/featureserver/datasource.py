from FeatureServer.DataSource import DataSource
from vectorformats.Feature import Feature
from vectorformats.Formats import WKT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import copy
import datetime

try:
    import decimal
except:
    pass
    
class GeoAlchemy (DataSource):
    """GeoAlchemy datasource. Setting up the table is beyond the scope of
       FeatureServer. However, GeoAlchemy supports table creation with
       geometry data types and can be used in a separate creation script."""
    
    def __init__(self, name, srid = 4326, fid = "gid", geometry = "the_geom", order = "", attribute_cols = '*', writable = True, encoding = "utf-8", session = None, **args):
        DataSource.__init__(self, name, **args)
        self.model          = args["model"]
        self.cls            = args["cls"]
        self.table          = args["layer"]
        self.fid_col        = fid
        self.geom_col       = geometry
        self.geom_rel       = args["geom_rel"]
        self.geom_cls       = args["geom_cls"]
        self.order          = order
        self.srid           = srid
        self.dburi          = args["dburi"]
        self.sql_echo       = args["sql_echo"] or False
        self.writable       = writable
        self.encoding       = encoding
        self.attribute_cols = attribute_cols
        self.session        = session

        if not self.session:
            self.engine = create_engine(self.dburi, echo=self.sql_echo)
            self.session = sessionmaker(bind=self.engine)()

    def begin (self):
        pass

    def commit (self):
        if self.writable:
            self.session.commit()

    def rollback (self):
        if self.writable:
            self.session.rollback()

    def create (self, action):
        model = __import__(self.model, fromlist=['*'])
        cls = getattr(model, self.cls)
        feature = action.feature
        obj =  cls()
        for prop in feature.properties.keys():
            setattr(obj, prop, feature.properties[prop])
        if self.geom_rel and self.geom_cls:
            geom_cls = getattr(model, self.geom_cls)
            geom_obj = geom_cls()
            setattr(geom_obj, self.geom_col, WKT.to_wkt(feature.geometry))
            getattr(obj, self.geom_rel).append(geom_obj)
            self.session.add(geom_obj)
        elif feature.geometry:
            setattr(obj, self.geom_col, WKT.to_wkt(feature.geometry))
        else:
            pass
        self.session.add(obj)
        return self.select(action)
        

    def update (self, action):
        model = __import__(self.model, fromlist=['*'])
        cls = getattr(model, self.cls)
        feature = action.feature
        obj = self.session.query(cls).get(int(action.id))
        for prop in feature.properties.keys():
            setattr(obj, prop, feature.properties[prop])
        if self.geom_rel and self.geom_cls:
            geom_obj = getattr(obj, self.geom_rel)
            setattr(geom_obj, self.geom_col, WKT.to_wkt(feature.geometry))
            self.session.add(geom_obj)
        elif feature.geometry:
            setattr(obj, self.geom_col, WKT.to_wkt(feature.geometry))
        else:
            pass
        self.session.add(obj)
        return self.select(action)
        
    def delete (self, action):
        model = __import__(self.model, fromlist=['*'])
        cls = getattr(model, self.cls)
        obj = self.session.query(cls).get(action.id)
        if self.geom_rel and self.geom_col:
            geom_obj = getattr(obj, self.geom_rel)
            self.session.delete(geom_obj[-1])
        self.session.delete(obj)
        return []

    def select (self, action):
        model = __import__(self.model, fromlist=['*'])
        cls = getattr(model, self.cls)
        if action.id is not None:
            result = [self.session.query(cls).get(action.id)]
        else:
            query = self.session.query(cls)
            if action.attributes:
                for attr in action.attributes:
                    query = query.filter(getattr(cls, attr)==action.attributes[attr])
            if self.order:
                query = query.order_by(self.order)
            if action.maxfeatures:
                query.limit(action.maxfeatures)
            else:   
                query.limit(1000)
            if action.startfeature:
                query.offset(action.startfeature)
            result = query.all()

        features = []
        for row in result:
            props = {}
            id = None
            geom = None
            if self.geom_rel and self.geom_cls:
                geom_obj = getattr(row, self.geom_rel)
                geom = WKT.from_wkt(self.session.scalar(getattr(geom_obj[-1], self.geom_col).wkt))
            for col in cls.__table__.c.keys():
                if col == self.fid_col:
                    id = getattr(row, col)
                elif col == self.geom_col:
                    geom = WKT.from_wkt(self.session.scalar(getattr(row, col).wkt))
                else:
                    if self.attribute_cols == '*' or col in self.attribute_cols:
                        props[col] = getattr(row, col)
            for key, value in props.items():
                if isinstance(value, str): 
                    props[key] = unicode(value, self.encoding)
                elif isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
                    # stringify datetimes 
                    props[key] = str(value)
                    
                try:
                    if isinstance(value, decimal.Decimal):
                        props[key] = unicode(str(value), self.encoding)
                except:
                    pass
                    
            if (geom):
                features.append( Feature( id, geom, props ) ) 
        return features
