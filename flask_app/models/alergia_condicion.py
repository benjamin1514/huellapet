from flask_app.config.mysqlconnection import connectToMySQL
class AlergiaCondicion:
    def __init__(self,data):
        for k,v in data.items(): setattr(self,k,v)
    @classmethod
    def get_by_mascota(cls,id_mascota):
        q="""SELECT a.*, u.nombre AS veterinario_nombre FROM alergia_condicion a JOIN usuario u ON u.id_usuario=a.id_veterinario WHERE a.id_mascota=%(id_mascota)s ORDER BY a.nombre_condicion;"""
        r=connectToMySQL("huellapet_db").query_db(q,{"id_mascota":id_mascota}); return [cls(x) for x in r]
