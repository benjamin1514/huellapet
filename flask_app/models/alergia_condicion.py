from flask_app.config.mysqlconnection import connectToMySQL
class AlergiaCondicion:
    def __init__(self,data):
        for k,v in data.items(): setattr(self,k,v)
    @classmethod
    def get_by_mascota(cls,id_mascota):
        q="""SELECT a.*, u.nombre AS veterinario_nombre FROM alergia_condicion a JOIN usuario u ON u.id_usuario=a.id_veterinario WHERE a.id_mascota=%(id_mascota)s ORDER BY a.nombre_condicion;"""
        r=connectToMySQL("huellapet_db").query_db(q,{"id_mascota":id_mascota}); return [cls(x) for x in r]

    # NUEVO: el veterinario registra, edita y borra alergias y condiciones
    @classmethod
    def get_by_id(cls, id_alergia_condicion):
        r = connectToMySQL("huellapet_db").query_db("SELECT * FROM alergia_condicion WHERE id_alergia_condicion=%(id)s;", {"id": id_alergia_condicion}) or []
        return cls(r[0]) if r else None

    @classmethod
    def save(cls, data):
        q = """INSERT INTO alergia_condicion (id_mascota,id_veterinario,nombre_condicion,gravedad,observaciones)
               VALUES (%(id_mascota)s,%(id_veterinario)s,%(nombre_condicion)s,%(gravedad)s,%(observaciones)s);"""
        return connectToMySQL("huellapet_db").query_db(q, data)

    @classmethod
    def update(cls, data):
        q = """UPDATE alergia_condicion SET nombre_condicion=%(nombre_condicion)s, gravedad=%(gravedad)s,
               observaciones=%(observaciones)s WHERE id_alergia_condicion=%(id_alergia_condicion)s;"""
        return connectToMySQL("huellapet_db").query_db(q, data)

    @classmethod
    def delete(cls, id_alergia_condicion):
        return connectToMySQL("huellapet_db").query_db("DELETE FROM alergia_condicion WHERE id_alergia_condicion=%(id)s;", {"id": id_alergia_condicion})
