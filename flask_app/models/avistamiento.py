from flask_app.config.mysqlconnection import connectToMySQL
class Avistamiento:
    def __init__(self,data):
        for k,v in data.items(): setattr(self,k,v)
    @classmethod
    def save(cls,data):
        q="""INSERT INTO avistamiento (id_mascota,latitud,longitud,precision_metros) VALUES (%(id_mascota)s,%(latitud)s,%(longitud)s,%(precision_metros)s);"""
        return connectToMySQL("huellapet_db").query_db(q,data)
    @classmethod
    def get_by_mascota(cls,id_mascota):
        r=connectToMySQL("huellapet_db").query_db("SELECT * FROM avistamiento WHERE id_mascota=%(id_mascota)s ORDER BY created_at DESC;",{"id_mascota":id_mascota}); return [cls(x) for x in r]
