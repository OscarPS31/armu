from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
                - "lactose_free"
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

def filter_by_time(df, max_time):
    """
    Regresa solo las recetas que se pueden preparar dentro del tiempo
    disponible del usuario.

    Args:
        df (pd.DataFrame): recipes_clean.csv cargado en un DataFrame, debe
            traer las columnas quick_15min, quick_30min, quick_60min.
        max_time: minutos disponibles para cocinar. Valores válidos:
            15, 30 o 60 .

    Returns:
       df con las recetas que se preparan en
            max_time minutos o menos.
    """
    if max_time == 15:
        columns = df[["quick_15min"]]
    elif max_time == 30:
        columns = df[["quick_15min","quick_30min"]]
    else:
        columns = df[["quick_15min", "quick_30min", "quick_60min"]]

    meets_time = columns.any(axis=1)

    return df[meets_time]

def rank_by_preference(df, user_text):
    """
    Ordena las recetas de mayor a menor similitud con lo que el usuario
    escribió, usando TF-IDF y similitud coseno sobre la columna search_text.

    Args:
        df (pd.DataFrame): recetas ya filtradas por restricciones y tiempo,
            debe traer la columna search_text.
        user_text (str): texto libre del usuario describiendo lo que quiere
            comer (ej. "algo ligero con pollo").

    Returns:
        pd.DataFrame: mismo df, con una columna nueva similarity_score,
            ordenado de mayor a menor similitud.
    """
    vectorizer = TfidfVectorizer()
    recipe_vectors = vectorizer.fit_transform(df['search_text'])

    user_vector = vectorizer.transform([user_text])

    similarity_scores = cosine_similarity(user_vector, recipe_vectors)

    df = df.copy()
    df['similarity_score'] = similarity_scores[0]

    return df.sort_values('similarity_score', ascending=False)

def build_weekly_menu(df, restriction, max_time, user_text):
    """
    Arma el menú semanal: filtra las recetas por restricciones y tiempo
    disponible, las ordena por qué tanto se parecen a lo que el usuario
    quiere comer, y se queda con las 7 mejores (una por día).

    Args:
        df (pd.DataFrame): recipes_clean.csv cargado en un DataFrame, debe
            traer las columnas necesarias para filter_by_restriction,
            filter_by_time y search_text para rank_by_preference.
        restriction: lista de restricciones alimenticias del usuario
            (mismos valores válidos que filter_by_restriction).
        max_time: minutos disponibles para cocinar (15, 30 o 60).
        user_text (str): texto libre del usuario describiendo lo que
            quiere comer (ej. "algo ligero con pollo").

    Returns:
        dict: weekly_menu con llaves monday...sunday, cada una con una
            lista de un recipe_id.
    """



    filter_restriction = filter_by_restriction(df, restriction)
    filter_time = filter_by_time(filter_restriction, max_time)
    rank_preference = rank_by_preference(filter_time, user_text)

    top7 = rank_preference.head(7)

    days = ["monday","tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    weekly_menu = {}

    for dia, id_receta in  zip(days, top7["id"]):
        weekly_menu[dia] = [id_receta]

    return weekly_menu
