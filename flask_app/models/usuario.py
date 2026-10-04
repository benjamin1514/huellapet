from flask_app.config.mysqlconnection import connectToMySQL


class Usuario:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @classmethod
    def _many(cls, query, data=None):
        resultados = connectToMySQL("huellapet_db").query_db(query, data or {}) or []
        return [cls(item) for item in resultados]

    @classmethod
    def get_all(cls):
        return cls._many("""
            SELECT u.*, tu.nombre_tipo AS tipo_nombre
            FROM usuario u
            JOIN tipo_usuario tu ON tu.id_tipo_usuario=u.id_tipo_usuario
            ORDER BY u.id_usuario;
        """)

    @classmethod
    def get_by_id(cls, id_usuario):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM usuario WHERE id_usuario=%(id_usuario)s;",
            {"id_usuario": id_usuario},
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_by_email(cls, email):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT * FROM usuario WHERE email=%(email)s;", {"email": email}
        ) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_with_type(cls, id_usuario):
        query = """
            SELECT u.*, tu.nombre_tipo AS tipo_nombre
            FROM usuario u
            JOIN tipo_usuario tu ON tu.id_tipo_usuario=u.id_tipo_usuario
            WHERE u.id_usuario=%(id_usuario)s;
        """
        resultados = connectToMySQL("huellapet_db").query_db(query, {"id_usuario": id_usuario}) or []
        return cls(resultados[0]) if resultados else None

    @classmethod
    def get_role_id(cls, nombre_tipo):
        resultados = connectToMySQL("huellapet_db").query_db(
            "SELECT id_tipo_usuario FROM tipo_usuario WHERE LOWER(TRIM(nombre_tipo))=LOWER(TRIM(%(nombre)s)) LIMIT 1;",
            {"nombre": nombre_tipo},
        ) or []
        return resultados[0]["id_tipo_usuario"] if resultados else None

    @classmethod
    def get_all_tutores(cls):
        return cls._many("""
            SELECT u.* FROM usuario u
            JOIN tipo_usuario tu ON tu.id_tipo_usuario=u.id_tipo_usuario
            WHERE LOWER(TRIM(tu.nombre_tipo))='tutor'
            ORDER BY u.nombre;
        """)

    @classmethod
    def update_password(cls, id_usuario, password):
        return connectToMySQL("huellapet_db").query_db(
            "UPDATE usuario SET password=%(password)s WHERE id_usuario=%(id_usuario)s;",
            {"id_usuario": id_usuario, "password": password},
        )

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO usuario (id_tipo_usuario,nombre,email,password,telefono,direccion)
            VALUES (%(id_tipo_usuario)s,%(nombre)s,%(email)s,%(password)s,%(telefono)s,%(direccion)s);
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE usuario SET nombre=%(nombre)s,email=%(email)s,telefono=%(telefono)s,
                direccion=%(direccion)s,id_tipo_usuario=%(id_tipo_usuario)s
            WHERE id_usuario=%(id_usuario)s;
        """
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_usuario):
        return connectToMySQL("huellapet_db").query_db(
            "DELETE FROM usuario WHERE id_usuario=%(id_usuario)s;", {"id_usuario": id_usuario}
        )
