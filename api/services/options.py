from api.schemas import RecommendationOptions


def get_recommendation_options() -> RecommendationOptions:
    return RecommendationOptions(
        cadenas=[
            "Walmart",
            "Soriana",
            "Chedraui",
        ],
        restricciones=[
            "vegetariano",
            "vegano",
            "sin_gluten",
        ],
        personas_min=1,
        personas_max=20,
    )
