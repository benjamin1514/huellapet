from flask_app.config.mysqlconnection import connectToMySQL


class PerfilVeterinario:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def get_all(cls):
        query = """
            SELECT pv.*, u.nombre AS usuario_nombre, u.email AS usuario_email
            FROM perfil_veterinario pv
            JOIN usuario u ON u.id_usuario=pv.id_usuario
            ORDER BY pv.id_perfil_veterinario;
        """
        resultados = connectToMySQL("huellapet_db").query_db(query) or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_perfil_veterinario):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM perfil_veterinario WHERE id_perfil_veterinario=%(id)s;",
            {"id": id_perfil_veterinario},
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_by_usuario(cls, id_usuario):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM perfil_veterinario WHERE id_usuario=%(id_usuario)s;",
            {"id_usuario": id_usuario},
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO perfil_veterinario (id_usuario,numero_colegiado,es_verificado,especialidad)
            VALUES (%(id_usuario)s,%(numero_colegiado)s,%(es_verificado)s,%(especialidad)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE perfil_veterinario SET numero_colegiado=%(numero_colegiado)s,
                especialidad=%(especialidad)s
            WHERE id_perfil_veterinario=%(id_perfil_veterinario)s;
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def verify(cls, id_perfil_veterinario, es_verificado):
        query = "UPDATE perfil_veterinario SET es_verificado=%(estado)s WHERE id_perfil_veterinario=%(id)s;"
        return connectToMySQL("huellapet_db").query_db(
            query, {"id": id_perfil_veterinario, "estado": int(bool(es_verificado))}
        )
