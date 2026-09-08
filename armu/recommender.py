def filter_by_restriction(df, restrictions):
    """
    La funcion lo que hace es regresar las rescetas que cumplan con todas las selecciones alimenticias seleccionadas por el usuario.

      Args:
        df (pd.DataFrame): recipes_clean.csv cargado en un DataFrame, debe
            traer las columnas is_vegan, is_vegetarian, is_gluten_free,
            is_dairy_free, is_nut_free, is_egg_free.
        restrictions: restricciones a aplicar. Valores válidos
            (el front debe mandar exactamente estos, como checkboxes):
                - "vegetarian"
                - "vegetarian"
                - "vegan"
                - "gluten_free"
                - "dairy_free"
                - "nut_free"
                - "egg_free"
    """
    columnas = ["is_" + r for r in restrictions]
    restricciones = df[columnas]
    matches_restrictions = restricciones.all(axis=1)
    return df[matches_restrictions]
