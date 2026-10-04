from flask_app.config.mysqlconnection import connectToMySQL


class ChatMensaje:
    """
    Representa y administra los registros de la tabla chat_mensaje.
    """

    def __init__(self, data):
        self.id_chat_mensaje = data["id_chat_mensaje"]
        self.id_mascota = data["id_mascota"]
        self.id_remitente = data["id_remitente"]
        self.id_destinatario = data["id_destinatario"]
        self.es_bot = data["es_bot"]
        self.mensaje = data["mensaje"]
        self.leido = data["leido"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]

    @classmethod
    def get_all(cls):
        query = """
            SELECT
                id_chat_mensaje,
                id_mascota,
                id_remitente,
                id_destinatario,
                es_bot,
                mensaje,
                leido,
                created_at,
                updated_at
            FROM chat_mensaje
            ORDER BY created_at ASC;
        """

        resultados = connectToMySQL("huellapet_db").query_db(query)
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_chat_mensaje):
        query = """
            SELECT
                id_chat_mensaje,
                id_mascota,
                id_remitente,
                id_destinatario,
                es_bot,
                mensaje,
                leido,
                created_at,
                updated_at
            FROM chat_mensaje
            WHERE id_chat_mensaje = %(id_chat_mensaje)s;
        """

        data = {"id_chat_mensaje": id_chat_mensaje}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_mascota(cls, id_mascota):
        query = """
            SELECT
                id_chat_mensaje,
                id_mascota,
                id_remitente,
                id_destinatario,
                es_bot,
                mensaje,
                leido,
                created_at,
                updated_at
            FROM chat_mensaje
            WHERE id_mascota = %(id_mascota)s
            ORDER BY created_at ASC;
        """

        data = {"id_mascota": id_mascota}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        return [cls(item) for item in resultados]

    @classmethod
    def get_conversation(cls, id_mascota, id_usuario):
        query = """
            SELECT
                id_chat_mensaje,
                id_mascota,
                id_remitente,
                id_destinatario,
                es_bot,
                mensaje,
                leido,
                created_at,
                updated_at
            FROM chat_mensaje
            WHERE id_mascota = %(id_mascota)s
            AND (
                id_remitente = %(id_usuario)s
                OR id_destinatario = %(id_usuario)s
                OR es_bot = 1
            )
            ORDER BY created_at ASC;
        """

        data = {
            "id_mascota": id_mascota,
            "id_usuario": id_usuario
        }

        resultados = connectToMySQL("huellapet_db").query_db(query, data)
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id_with_users(cls, id_chat_mensaje):
        query = """
            SELECT
                chat_mensaje.id_chat_mensaje,
                chat_mensaje.id_mascota,
                chat_mensaje.id_remitente,
                chat_mensaje.id_destinatario,
                chat_mensaje.es_bot,
                chat_mensaje.mensaje,
                chat_mensaje.leido,
                chat_mensaje.created_at,
                chat_mensaje.updated_at,

                remitente.nombre AS remitente_nombre,
                destinatario.nombre AS destinatario_nombre,
                mascota.nombre AS mascota_nombre

            FROM chat_mensaje

            INNER JOIN mascota
                ON mascota.id_mascota = chat_mensaje.id_mascota

            INNER JOIN usuario AS remitente
                ON remitente.id_usuario = chat_mensaje.id_remitente

            LEFT JOIN usuario AS destinatario
                ON destinatario.id_usuario = chat_mensaje.id_destinatario

            WHERE chat_mensaje.id_chat_mensaje =
                %(id_chat_mensaje)s;
        """

        data = {"id_chat_mensaje": id_chat_mensaje}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if not resultados:
            return None

        mensaje = cls(resultados[0])
        mensaje.remitente_nombre = resultados[0]["remitente_nombre"]
        mensaje.destinatario_nombre = resultados[0]["destinatario_nombre"]
        mensaje.mascota_nombre = resultados[0]["mascota_nombre"]

        return mensaje

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO chat_mensaje
            (
                id_mascota,
                id_remitente,
                id_destinatario,
                es_bot,
                mensaje,
                leido
            )
            VALUES
            (
                %(id_mascota)s,
                %(id_remitente)s,
                %(id_destinatario)s,
                %(es_bot)s,
                %(mensaje)s,
                %(leido)s
            );
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def mark_as_read(cls, id_chat_mensaje):
        query = """
            UPDATE chat_mensaje
            SET leido = 1
            WHERE id_chat_mensaje = %(id_chat_mensaje)s;
        """

        data = {"id_chat_mensaje": id_chat_mensaje}
        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_chat_mensaje):
        query = """
            DELETE FROM chat_mensaje
            WHERE id_chat_mensaje = %(id_chat_mensaje)s;
        """

        data = {"id_chat_mensaje": id_chat_mensaje}
        return connectToMySQL("huellapet_db").query_db(query, data)
