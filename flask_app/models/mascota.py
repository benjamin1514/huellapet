import secrets
from flask_app.config.mysqlconnection import connectToMySQL


class Mascota:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def _one(cls, query, data=None):
        resultados = connectToMySQL("huellapet_db").query_db(query, data or {}) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_by_id(cls, id_mascota):
        return cls._one(
            "SELECT * FROM mascota WHERE id_mascota=%(id_mascota)s;",
            {"id_mascota": id_mascota},
        )

    @classmethod
    def get_by_codigo(cls, codigo):
        query = """
            SELECT m.*, te.nombre_tipo AS especie, ts.nombre_tipo AS sexo
            FROM mascota m
            JOIN tipo_especie te ON te.id_tipo_especie=m.id_tipo_especie
            JOIN tipo_sexo ts ON ts.id_tipo_sexo=m.id_tipo_sexo
            WHERE m.codigo_huellapet=%(codigo)s;
        """
        return cls._one(query, {"codigo": codigo})

    @classmethod
    def get_by_nfc(cls, codigo):
        query = """
            SELECT m.*, te.nombre_tipo AS especie, ts.nombre_tipo AS sexo
            FROM mascota m
            JOIN tipo_especie te ON te.id_tipo_especie=m.id_tipo_especie
            JOIN tipo_sexo ts ON ts.id_tipo_sexo=m.id_tipo_sexo
            LEFT JOIN dispositivo_nfc d ON d.id_mascota=m.id_mascota
            WHERE m.codigo_huellapet=%(codigo)s
               OR d.codigo_uid=%(codigo)s
               OR d.token_qr=%(codigo)s
            LIMIT 1;
        """
        return cls._one(query, {"codigo": codigo})

    @classmethod
    def get_by_tutor(cls, id_tutor):
        query = "SELECT * FROM mascota WHERE id_tutor=%(id_tutor)s ORDER BY nombre;"
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_tutor": id_tutor}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_all_with_details(cls):
        query = """
            SELECT m.*, u.nombre AS tutor_nombre,
                   te.nombre_tipo AS especie, ts.nombre_tipo AS sexo
            FROM mascota m
            JOIN usuario u ON u.id_usuario=m.id_tutor
            JOIN tipo_especie te ON te.id_tipo_especie=m.id_tipo_especie
            JOIN tipo_sexo ts ON ts.id_tipo_sexo=m.id_tipo_sexo
            ORDER BY m.nombre;
        """
        resultados = connectToMySQL("huellapet_db").query_db(query) or []
        return [cls(item) for item in resultados]

    @classmethod
    def generar_codigo(cls):
        while True:
            codigo = "HP-" + secrets.token_hex(4).upper()
            if cls.get_by_codigo(codigo) is None:
                return codigo

    @classmethod
    def save(cls, data):
        payload = dict(data)
        payload.setdefault("codigo_huellapet", cls.generar_codigo())
        query = """
            INSERT INTO mascota
            (id_tutor,id_tipo_especie,id_tipo_sexo,codigo_huellapet,nombre,raza,
             fecha_nacimiento,peso_kg,descripcion,foto_url)
            VALUES
            (%(id_tutor)s,%(id_tipo_especie)s,%(id_tipo_sexo)s,%(codigo_huellapet)s,
             %(nombre)s,%(raza)s,%(fecha_nacimiento)s,%(peso_kg)s,%(descripcion)s,%(foto_url)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, payload)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE mascota SET
                id_tutor=%(id_tutor)s,
                id_tipo_especie=%(id_tipo_especie)s,
                id_tipo_sexo=%(id_tipo_sexo)s,
                nombre=%(nombre)s,
                raza=%(raza)s,
                fecha_nacimiento=%(fecha_nacimiento)s,
                peso_kg=%(peso_kg)s,
                descripcion=%(descripcion)s
            WHERE id_mascota=%(id_mascota)s;
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update_foto(cls, id_mascota, foto_url):
        query = "UPDATE mascota SET foto_url=%(foto_url)s WHERE id_mascota=%(id_mascota)s;"
        return connectToMySQL("huellapet_db").query_db(
            query, {"id_mascota": id_mascota, "foto_url": foto_url}
        )

    @classmethod
    def delete(cls, id_mascota):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM mascota WHERE id_mascota=%(id_mascota)s;",
            {"id_mascota": id_mascota},
        )
