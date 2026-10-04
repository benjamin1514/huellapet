from flask_app.config.mysqlconnection import connectToMySQL


class Documento:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_by_id(cls, id_documento):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM documento WHERE id_documento=%(id_documento)s;",
            {"id_documento": id_documento},
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_by_mascota(cls, id_mascota):
        query = """
            SELECT d.*, td.nombre_tipo AS tipo
            FROM documento d
            JOIN tipo_documento td ON td.id_tipo_documento=d.id_tipo_documento
            WHERE d.id_mascota=%(id_mascota)s
            ORDER BY d.created_at DESC;
        """
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_mascota": id_mascota}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO documento (id_mascota,id_tipo_documento,nombre_doc,archivo_url)
            VALUES (%(id_mascota)s,%(id_tipo_documento)s,%(nombre_doc)s,%(archivo_url)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_documento):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM documento WHERE id_documento=%(id_documento)s;",
            {"id_documento": id_documento},
        )
