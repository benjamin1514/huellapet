from flask_app.config.mysqlconnection import connectToMySQL
class UbicacionExtravio:
    def __init__(self,data):
        for k,v in data.items(): setattr(self,k,v)
    @classmethod
    def get_active_by_mascota(cls,id_mascota):
        q="""SELECT * FROM ubicacion_extravio WHERE id_mascota=%(id_mascota)s AND reportado_extraviado=1 ORDER BY created_at DESC LIMIT 1;"""
        r=connectToMySQL("huellapet_db").query_db(q,{"id_mascota":id_mascota}); return cls(r[0]) if r else None
    @classmethod
    def set_estado(cls,data):
        actual=cls.get_active_by_mascota(data['id_mascota'])
        if actual:
            q="""UPDATE ubicacion_extravio SET reportado_extraviado=%(reportado_extraviado)s, notificaciones_activas=%(notificaciones_activas)s, fecha_registro=NOW() WHERE id_ubicacion_extravio=%(id_ubicacion_extravio)s;"""
            data=dict(data,id_ubicacion_extravio=actual.id_ubicacion_extravio)
        else:
            q="""INSERT INTO ubicacion_extravio (id_mascota,reportado_extraviado,fecha_registro,notificaciones_activas) VALUES (%(id_mascota)s,%(reportado_extraviado)s,NOW(),%(notificaciones_activas)s);"""
        return connectToMySQL("huellapet_db").query_db(q,data)
