from flask_app.config.mysqlconnection import connectToMySQL


class HistorialMedico:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_by_id(cls, id_historial_medico):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM historial_medico WHERE id_historial_medico=%(id)s;",
            {"id": id_historial_medico},
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_by_mascota(cls, id_mascota):
        query = """
            SELECT h.*, th.nombre_tipo AS tipo, u.nombre AS veterinario_nombre
            FROM historial_medico h
            JOIN tipo_historial th ON th.id_tipo_historial=h.id_tipo_historial
            JOIN usuario u ON u.id_usuario=h.id_veterinario
            WHERE h.id_mascota=%(id_mascota)s
            ORDER BY h.fecha_atencion DESC, h.id_historial_medico DESC;
        """
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_mascota": id_mascota}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO historial_medico
            (id_mascota,id_veterinario,id_tipo_historial,titulo,descripcion,fecha_atencion,proxima_fecha)
            VALUES (%(id_mascota)s,%(id_veterinario)s,%(id_tipo_historial)s,%(titulo)s,
                    %(descripcion)s,%(fecha_atencion)s,%(proxima_fecha)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE historial_medico SET id_tipo_historial=%(id_tipo_historial)s,
                titulo=%(titulo)s,descripcion=%(descripcion)s,
                fecha_atencion=%(fecha_atencion)s,proxima_fecha=%(proxima_fecha)s
            WHERE id_historial_medico=%(id_historial_medico)s;
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_historial_medico):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM historial_medico WHERE id_historial_medico=%(id)s;",
            {"id": id_historial_medico},
        )
