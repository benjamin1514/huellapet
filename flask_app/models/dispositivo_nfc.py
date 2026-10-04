from flask_app.config.mysqlconnection import connectToMySQL


class DispositivoNFC:
    """
    Representa y administra los registros de dispositivo_nfc.
    """

    def __init__(self, data):
        self.id_dispositivo_nfc = data["id_dispositivo_nfc"]
        self.id_mascota = data["id_mascota"]
        self.id_tipo_estado_dispositivo = data["id_tipo_estado_dispositivo"]
        self.codigo_uid = data["codigo_uid"]
        self.token_qr = data["token_qr"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]

    @classmethod
    def get_all(cls):
        query = """
            SELECT
                id_dispositivo_nfc,
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr,
                created_at,
                updated_at
            FROM dispositivo_nfc
            ORDER BY id_dispositivo_nfc;
        """

        resultados = connectToMySQL("huellapet_db").query_db(query)
        return [cls(item) for item in resultados]

    @classmethod
    def get_by_id(cls, id_dispositivo_nfc):
        query = """
            SELECT
                id_dispositivo_nfc,
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr,
                created_at,
                updated_at
            FROM dispositivo_nfc
            WHERE id_dispositivo_nfc = %(id_dispositivo_nfc)s;
        """

        data = {"id_dispositivo_nfc": id_dispositivo_nfc}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_uid(cls, codigo_uid):
        query = """
            SELECT
                id_dispositivo_nfc,
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr,
                created_at,
                updated_at
            FROM dispositivo_nfc
            WHERE codigo_uid = %(codigo_uid)s;
        """

        data = {"codigo_uid": codigo_uid}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_qr(cls, token_qr):
        query = """
            SELECT
                id_dispositivo_nfc,
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr,
                created_at,
                updated_at
            FROM dispositivo_nfc
            WHERE token_qr = %(token_qr)s;
        """

        data = {"token_qr": token_qr}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_mascota(cls, id_mascota):
        query = """
            SELECT
                id_dispositivo_nfc,
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr,
                created_at,
                updated_at
            FROM dispositivo_nfc
            WHERE id_mascota = %(id_mascota)s;
        """

        data = {"id_mascota": id_mascota}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if resultados:
            return cls(resultados[0])

        return None

    @classmethod
    def get_by_id_with_details(cls, id_dispositivo_nfc):
        query = """
            SELECT
                dispositivo_nfc.id_dispositivo_nfc,
                dispositivo_nfc.id_mascota,
                dispositivo_nfc.id_tipo_estado_dispositivo,
                dispositivo_nfc.codigo_uid,
                dispositivo_nfc.token_qr,
                dispositivo_nfc.created_at,
                dispositivo_nfc.updated_at,

                mascota.nombre AS mascota_nombre,
                tipo_estado_dispositivo.nombre AS estado_nombre

            FROM dispositivo_nfc

            LEFT JOIN mascota
                ON mascota.id_mascota = dispositivo_nfc.id_mascota

            LEFT JOIN tipo_estado_dispositivo
                ON tipo_estado_dispositivo.id_tipo_estado_dispositivo =
                    dispositivo_nfc.id_tipo_estado_dispositivo

            WHERE dispositivo_nfc.id_dispositivo_nfc =
                %(id_dispositivo_nfc)s;
        """

        data = {"id_dispositivo_nfc": id_dispositivo_nfc}
        resultados = connectToMySQL("huellapet_db").query_db(query, data)

        if not resultados:
            return None

        dispositivo = cls(resultados[0])
        dispositivo.mascota_nombre = resultados[0]["mascota_nombre"]
        dispositivo.estado_nombre = resultados[0]["estado_nombre"]

        return dispositivo

    @classmethod
    def save(cls, data):
        query = """
            INSERT INTO dispositivo_nfc
            (
                id_mascota,
                id_tipo_estado_dispositivo,
                codigo_uid,
                token_qr
            )
            VALUES
            (
                %(id_mascota)s,
                %(id_tipo_estado_dispositivo)s,
                %(codigo_uid)s,
                %(token_qr)s
            );
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def update(cls, data):
        query = """
            UPDATE dispositivo_nfc
            SET
                id_mascota = %(id_mascota)s,
                id_tipo_estado_dispositivo = %(id_tipo_estado_dispositivo)s,
                codigo_uid = %(codigo_uid)s,
                token_qr = %(token_qr)s
            WHERE id_dispositivo_nfc = %(id_dispositivo_nfc)s;
        """

        return connectToMySQL("huellapet_db").query_db(query, data)

    @classmethod
    def delete(cls, id_dispositivo_nfc):
        query = """
            DELETE FROM dispositivo_nfc
            WHERE id_dispositivo_nfc = %(id_dispositivo_nfc)s;
        """

        data = {"id_dispositivo_nfc": id_dispositivo_nfc}
        return connectToMySQL("huellapet_db").query_db(query, data)
