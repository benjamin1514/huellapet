from flask_app.config.mysqlconnection import connectToMySQL


class Cita:
    """Citas médicas agendadas con una clínica (tabla cita)."""

    CONSULTA = """
        SELECT c.*, m.nombre AS mascota_nombre, m.id_tutor, cl.nombre AS clinica_nombre,
               u.nombre AS tutor_nombre
        FROM cita c
        JOIN mascota m ON m.id_mascota = c.id_mascota
        JOIN clinica cl ON cl.id_clinica = c.id_clinica
        JOIN usuario u ON u.id_usuario = m.id_tutor
    """

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_all(cls):
        resultados = connectToMySQL("huellapet_db").query_db(cls.CONSULTA + " ORDER BY c.fecha_hora;") or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_tutor(cls, id_tutor):
        query = cls.CONSULTA + " WHERE m.id_tutor=%(id_tutor)s ORDER BY c.fecha_hora;"
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_tutor": id_tutor}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_cita):
        query = cls.CONSULTA + " WHERE c.id_cita=%(id)s;"
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id": id_cita}) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO cita (id_mascota, id_clinica, fecha_hora, motivo)
            VALUES (%(id_mascota)s, %(id_clinica)s, %(fecha_hora)s, %(motivo)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def set_estado(cls, id_cita, estado):
        return connectToMySQL("huellapet_db").query_db(
            "UPDATE cita SET estado=%(estado)s WHERE id_cita=%(id)s;", {"id": id_cita, "estado": estado})
