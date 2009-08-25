from FeatureServer.DataSource import DataSource
from vectorformats.Feature import Feature
from vectorformats.Formats import WKT
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from geoalchemy.base import WKTSpatialElement, _to_gis

import copy
import datetime
import operator

try:
    import decimal
except:
    pass
    
class GeoAlchemy (DataSource):
    """GeoAlchemy datasource. Setting up the table is beyond the scope of
       FeatureServer. However, GeoAlchemy supports table creation with
       geometry data types and can be used in a separate creation script."""

    query_action_types = ['eq', 'ne', 'lt', 'gt', 'ilike', 'like', 'gte', 'lte']

    query_operators = {
        'eq': operator.eq,
        'ne': operator.ne,
        'lt': operator.lt,
        'gt': operator.gt,
        'lte': operator.le,
        'gte': operator.ge,
    }

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

    def feature_predicate(self, key,operator_name,value):
        if operator_name == 'like':
            return key.like('%'+value+'%')
        elif operator_name == 'ilike':
            return key.ilike('%'+value+'%')
        else:
            return self.query_operators[operator_name](key,value)

    def bbox2wkt(self, bbox):
        return "LINESTRING((%s %s, %s %s, %s %s, %s %s, %s %s))" % (bbox[0],
        bbox[1],bbox[2],bbox[1],bbox[2],bbox[3],bbox[0],bbox[3],bbox[0],bbox[1])

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
            try:
                getattr(obj, self.geom_rel).append(geom_obj)
            except:
                # Handle specific exception
                setattr(obj, self.geom_rel, geom_obj)
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
            if isinstance(geom_obj, (tuple, list, dict, set)):
                #TODO Should all related objects be purged
                self.session.delete(geom_obj[-1])
            else:
                self.session.delete(geom_obj)
        self.session.delete(obj)
        return []

    def select (self, action):
        model = __import__(self.model, fromlist=['*'])
        cls = getattr(model, self.cls)
        geom_cls = None
        if self.geom_cls:
            geom_cls = getattr(model, self.geom_cls)
        if action.id is not None:
            result = [self.session.query(cls).get(action.id)]
        else:
            if self.geom_rel and self.geom_cls:
                query = self.session.query(cls, geom_cls)
            else:
                query = self.session.query(cls)
            if action.attributes:
                query = query.filter(
                    and_(
                        *[self.feature_predicate(getattr(cls, k), v['type'], v['value'])
				for k, v in action.attributes.iteritems()]
                    )
                )
            if action.bbox:
                if self.geom_rel and self.geom_cls:
                    geom_element = getattr(geom_cls, self.geom_col)
                else:
                    geom_element = getattr(cls, self.geom_col)
                query = query.filter(geom_element.intersects(
                    _to_gis(self.bbox2wkt(action.bbox))))
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
                if not geom_obj:
                    continue
                elif isinstance(geom_obj, (tuple, list, dict, set)):
                    geom = WKT.from_wkt(self.session.scalar(getattr(geom_obj[-1], self.geom_col).wkt))
                else:
                    geom = WKT.from_wkt(self.session.scalar(getattr(geom_obj, self.geom_col).wkt))
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
