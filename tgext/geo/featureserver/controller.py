from tg import config, request, response, expose
from tg.controllers import TGController, CUSTOM_CONTENT_TYPE
from FeatureServer.Server import Server
import cgi as cgimod
from datasource import GeoAlchemy


class FeatureServerController(TGController):

    def __init__(self, name, session, allow_only=None):
        self.model = config.get("geo.%s.model"%name, None)
        self.cls = config.get("geo.%s.cls"%name, None)
        self.table = config.get("geo.%s.table"%name, self.cls.lower())
        self.layer = name
        self.fid = config.get("geo.%s.fid"%name, "gid")
        self.geometry = config.get("geo.%s.geometry"%name, "the_geom")
        self.geom_rel = config.get("geo.%s.geom_rel"%name, None)
        self.geom_cls = config.get("geo.%s.geom_cls"%name, None)
        self.join_condition = config.get("geo.%s.join_condition"%name, None)
        self.order = config.get("geo.%s.order"%name, self.fid)
        self.srid = config.get("geo.%s.srid"%name, 4326)
        self.dburi = config.get("sqlalchemy.url", None)
        self.dburi = config.get("geo.%s.dburi"%name, self.dburi)
        self.sql_echo = config.get("sqlalchemy.echo", None)
        self.writable = config.get("geo.%s.writable"%name, False)
        self.encoding = config.get("geo.%s.encoding"%name, "utf-8")
        self.attribute_cols = config.get("geo.%s.attribute_cols"%name, "*")
        self.attribute_ignore = config.get("geo.%s.attribute_ignore"%name, [])

        datasource = GeoAlchemy(
            self.layer, 
            srid = self.srid,
            fid = self.fid,
            geometry = self.geometry,
            order = self.order,
            attribute_cols = self.attribute_cols,
            attribute_ignore = self.attribute_ignore,
            writable = self.writable,
            encoding = self.encoding,
            session = session,
            dburi = self.dburi,
            sql_echo = self.sql_echo,
            layer = self.layer,
            model = self.model,
            geom_rel = self.geom_rel,
            geom_cls = self.geom_cls,
            join_condition = self.join_condition,
            cls = self.cls
        )

        self.server = Server({self.layer: datasource})
        self.allow_only = allow_only
        super(FeatureServerController, self).__init__()

    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def default(self, *args, **kw):
        params = {}
        if request.environ.has_key('QUERY_STRING'):
            for key, value in cgimod.parse_qsl(
                request.environ['QUERY_STRING'], keep_blank_values=True):
                params[key.lower()] = value

        if request.method == 'GET':
             response.content_type, resp = self.server.dispatchRequest(
                path_info=request.path_info, params=params, base_path= "")
             return resp
        elif request.method == 'POST':
            if request.POST.keys():
                data = request.POST.keys()[0]
            else:
                data = request.body
            request.content_type, resp = self.server.dispatchRequest(
                params=params, path_info=request.path_info,
                base_path="", post_data=data, request_method="POST")
            return resp
        elif request.method == 'DELETE':
            response.content_type, resp = self.server.dispatchRequest(
                params=params, path_info=request.path_info,
                base_path="", post_data="", request_method="DELETE")
            return resp
        else:
            flash("Unsupported method type %s" % request.method)
            redirect (request.referer)

