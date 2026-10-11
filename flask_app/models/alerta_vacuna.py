from flask_app.config.mysqlconnection import connectToMySQL


class AlertaVacuna:
    """Alertas de vacuna que programa el tutor (tabla alerta_vacuna)."""

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_by_mascota(cls, id_mascota):
        query = "SELECT * FROM alerta_vacuna WHERE id_mascota=%(id_mascota)s ORDER BY fecha_alerta;"
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_mascota": id_mascota}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_alerta_vacuna):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM alerta_vacuna WHERE id_alerta_vacuna=%(id)s;", {"id": id_alerta_vacuna}) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO alerta_vacuna (id_mascota, titulo, fecha_alerta)
            VALUES (%(id_mascota)s, %(titulo)s, %(fecha_alerta)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_alerta_vacuna):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM alerta_vacuna WHERE id_alerta_vacuna=%(id)s;", {"id": id_alerta_vacuna})
