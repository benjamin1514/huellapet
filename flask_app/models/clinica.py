from flask_app.config.mysqlconnection import connectToMySQL


class Clinica:
    """Clínicas asociadas donde se pueden agendar citas (tabla clinica)."""

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_all(cls):
        resultados = connectToMySQL("huellapet_db").query_db("SELECT * FROM clinica ORDER BY nombre;") or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_clinica):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM clinica WHERE id_clinica=%(id)s;", {"id": id_clinica}) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO clinica (nombre, direccion, telefono)
            VALUES (%(nombre)s, %(direccion)s, %(telefono)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_clinica):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM clinica WHERE id_clinica=%(id)s;", {"id": id_clinica})
