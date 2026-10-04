from flask_app.config.mysqlconnection import connectToMySQL


class Pago:
    """
    Representa y administra los registros de la tabla pago.
    """

    def __init__(self, data):
        self.id_pago = data["id_pago"]
        self.id_suscripcion = data["id_suscripcion"]
        self.id_tipo_estado_pago = data["id_tipo_estado_pago"]
        self.monto = data["monto"]
        self.metodo_pago = data["metodo_pago"]
        self.fecha_pago = data["fecha_pago"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]

    @classmethod
    def get_all(cls):
        query = """
            SELECT
                id_pago,
                id_suscripcion,
                id_tipo_estado_pago,
                monto,
                metodo_pago,
                fecha_pago,
                created_at,
                updated_at
            FROM pago
            ORDER BY fecha_pago DESC;
        """

        resultados = connectToMySQL("huellapet_db").query_db(query)
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_pago):
        query = """
            SELECT
                id_pago,
                id_suscripcion,
                id_tipo_estado_pago,
                monto,
                metodo_pago,
                fecha_pago,
                created_at,
                updated_at
            FROM pago
            WHERE id_pago = %(id_pago)s;
        """

        data = {"id_pago": id_pago}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_suscripcion(cls, id_suscripcion):
        query = """
            SELECT
                id_pago,
                id_suscripcion,
                id_tipo_estado_pago,
                monto,
                metodo_pago,
                fecha_pago,
                created_at,
                updated_at
            FROM pago
            WHERE id_suscripcion = %(id_suscripcion)s
            ORDER BY fecha_pago DESC;
        """

        data = {"id_suscripcion": id_suscripcion}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id_with_details(cls, id_pago):
        query = """
            SELECT
                pago.id_pago,
                pago.id_suscripcion,
                pago.id_tipo_estado_pago,
                pago.monto,
                pago.metodo_pago,
                pago.fecha_pago,
                pago.created_at,
                pago.updated_at,

                suscripcion.id_usuario,
                usuario.nombre AS usuario_nombre,
                usuario.email AS usuario_email,
                tipo_estado_pago.nombre AS estado_nombre

            FROM pago

            INNER JOIN suscripcion
                ON suscripcion.id_suscripcion = pago.id_suscripcion

            INNER JOIN usuario
                ON usuario.id_usuario = suscripcion.id_usuario

            LEFT JOIN tipo_estado_pago
                ON tipo_estado_pago.id_tipo_estado_pago =
                    pago.id_tipo_estado_pago

            WHERE pago.id_pago = %(id_pago)s;
        """

        data = {"id_pago": id_pago}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if not resultados:
            return None

        pago = cls(resultados[0])
        pago.id_usuario = resultados[0]["id_usuario"]
        pago.usuario_nombre = resultados[0]["usuario_nombre"]
        pago.usuario_email = resultados[0]["usuario_email"]
        pago.estado_nombre = resultados[0]["estado_nombre"]

        return pago

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO pago
            (
                id_suscripcion,
                id_tipo_estado_pago,
                monto,
                metodo_pago,
                fecha_pago
            )
            VALUES
            (
                %(id_suscripcion)s,
                %(id_tipo_estado_pago)s,
                %(monto)s,
                %(metodo_pago)s,
                %(fecha_pago)s
            );
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE pago
            SET
                id_tipo_estado_pago = %(id_tipo_estado_pago)s,
                monto = %(monto)s,
                metodo_pago = %(metodo_pago)s,
                fecha_pago = %(fecha_pago)s
            WHERE id_pago = %(id_pago)s;
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_pago):
        query = """
            DELETE FROM pago
            WHERE id_pago = %(id_pago)s;
        """

        data = {"id_pago": id_pago}
        return connectToMySQL("huellapet_db").query_db(query, data)
