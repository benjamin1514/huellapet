from flask_app.config.mysqlconnection import connectToMySQL


class Suscripcion:
    """
    Representa y administra los registros de la tabla suscripcion.
    """

    def __init__(self, data):
        self.id_suscripcion = data["id_suscripcion"]
        self.id_usuario = data["id_usuario"]
        self.id_tipo_plan = data["id_tipo_plan"]
        self.id_tipo_estado_suscripcion = data["id_tipo_estado_suscripcion"]
        self.fecha_inicio = data["fecha_inicio"]
        self.fecha_fin = data["fecha_fin"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]

    @classmethod
    def get_all(cls):
        query = """
            SELECT
                id_suscripcion,
                id_usuario,
                id_tipo_plan,
                id_tipo_estado_suscripcion,
                fecha_inicio,
                fecha_fin,
                created_at,
                updated_at
            FROM suscripcion
            ORDER BY id_suscripcion;
        """

        resultados = connectToMySQL("huellapet_db").query_db(query)
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_suscripcion):
        query = """
            SELECT
                id_suscripcion,
                id_usuario,
                id_tipo_plan,
                id_tipo_estado_suscripcion,
                fecha_inicio,
                fecha_fin,
                created_at,
                updated_at
            FROM suscripcion
            WHERE id_suscripcion = %(id_suscripcion)s;
        """

        data = {"id_suscripcion": id_suscripcion}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_usuario(cls, id_usuario):
        query = """
            SELECT
                id_suscripcion,
                id_usuario,
                id_tipo_plan,
                id_tipo_estado_suscripcion,
                fecha_inicio,
                fecha_fin,
                created_at,
                updated_at
            FROM suscripcion
            WHERE id_usuario = %(id_usuario)s
            ORDER BY fecha_inicio DESC;
        """

        data = {"id_usuario": id_usuario}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        return [cls(item) for item in resultados]

    @classmethod
    def get_active_by_usuario(cls, id_usuario):
        query = """
            SELECT
                suscripcion.id_suscripcion,
                suscripcion.id_usuario,
                suscripcion.id_tipo_plan,
                suscripcion.id_tipo_estado_suscripcion,
                suscripcion.fecha_inicio,
                suscripcion.fecha_fin,
                suscripcion.created_at,
                suscripcion.updated_at,
                tipo_plan.nombre AS plan_nombre,
                tipo_estado_suscripcion.nombre AS estado_nombre
            FROM suscripcion
            LEFT JOIN tipo_plan
                ON tipo_plan.id_tipo_plan = suscripcion.id_tipo_plan
            LEFT JOIN tipo_estado_suscripcion
                ON tipo_estado_suscripcion.id_tipo_estado_suscripcion =
                    suscripcion.id_tipo_estado_suscripcion
            WHERE suscripcion.id_usuario = %(id_usuario)s
            AND (
                suscripcion.fecha_fin IS NULL
                OR suscripcion.fecha_fin >= CURRENT_DATE()
            )
            ORDER BY suscripcion.fecha_inicio DESC
            LIMIT 1;
        """

        data = {"id_usuario": id_usuario}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if not resultados:
            return None

        suscripcion = cls(resultados[0])
        suscripcion.plan_nombre = resultados[0]["plan_nombre"]
        suscripcion.estado_nombre = resultados[0]["estado_nombre"]

        return suscripcion

    @classmethod
    def get_by_id_with_details(cls, id_suscripcion):
        query = """
            SELECT
                suscripcion.id_suscripcion,
                suscripcion.id_usuario,
                suscripcion.id_tipo_plan,
                suscripcion.id_tipo_estado_suscripcion,
                suscripcion.fecha_inicio,
                suscripcion.fecha_fin,
                suscripcion.created_at,
                suscripcion.updated_at,

                usuario.nombre AS usuario_nombre,
                usuario.email AS usuario_email,
                tipo_plan.nombre AS plan_nombre,
                tipo_estado_suscripcion.nombre AS estado_nombre

            FROM suscripcion

            INNER JOIN usuario
                ON usuario.id_usuario = suscripcion.id_usuario

            LEFT JOIN tipo_plan
                ON tipo_plan.id_tipo_plan = suscripcion.id_tipo_plan

            LEFT JOIN tipo_estado_suscripcion
                ON tipo_estado_suscripcion.id_tipo_estado_suscripcion =
                    suscripcion.id_tipo_estado_suscripcion

            WHERE suscripcion.id_suscripcion = %(id_suscripcion)s;
        """

        data = {"id_suscripcion": id_suscripcion}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if not resultados:
            return None

        suscripcion = cls(resultados[0])
        suscripcion.usuario_nombre = resultados[0]["usuario_nombre"]
        suscripcion.usuario_email = resultados[0]["usuario_email"]
        suscripcion.plan_nombre = resultados[0]["plan_nombre"]
        suscripcion.estado_nombre = resultados[0]["estado_nombre"]

        return suscripcion

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO suscripcion
            (
                id_usuario,
                id_tipo_plan,
                id_tipo_estado_suscripcion,
                fecha_inicio,
                fecha_fin
            )
            VALUES
            (
                %(id_usuario)s,
                %(id_tipo_plan)s,
                %(id_tipo_estado_suscripcion)s,
                %(fecha_inicio)s,
                %(fecha_fin)s
            );
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE suscripcion
            SET
                id_tipo_plan = %(id_tipo_plan)s,
                id_tipo_estado_suscripcion = %(id_tipo_estado_suscripcion)s,
                fecha_inicio = %(fecha_inicio)s,
                fecha_fin = %(fecha_fin)s
            WHERE id_suscripcion = %(id_suscripcion)s;
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_suscripcion):
        query = """
            DELETE FROM suscripcion
            WHERE id_suscripcion = %(id_suscripcion)s;
        """

        data = {"id_suscripcion": id_suscripcion}
        return connectToMySQL("huellapet_db").query_db(query, data)
