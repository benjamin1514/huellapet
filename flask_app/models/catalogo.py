from flask_app.config.mysqlconnection import connectToMySQL


class Catalogo:
    PERMITIDOS = {
        'tipo_especie': 'id_tipo_especie',
        'tipo_sexo': 'id_tipo_sexo',
        'tipo_historial': 'id_tipo_historial',
        'tipo_documento': 'id_tipo_documento',
    }

    @classmethod
    def _all(cls, tabla):
        id_columna = cls.PERMITIDOS.get(tabla)
        if not id_columna:
            return []
        query = f"SELECT {id_columna} AS id, nombre_tipo AS nombre FROM {tabla} ORDER BY {id_columna};"
        return connectToMySQL('huellapet_db').query_db(query) or []

    @classmethod
    def especies(cls): return cls._all('tipo_especie')
    @classmethod
    def sexos(cls): return cls._all('tipo_sexo')
    @classmethod
    def tipos_historial(cls): return cls._all('tipo_historial')
    @classmethod
    def tipos_documento(cls): return cls._all('tipo_documento')
