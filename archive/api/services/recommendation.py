from api.fixtures import FAKE_MENU, FAKE_CART, EMPTY_MENU, OVER_BUDGET_CART
from api.schemas import RecommendationRequest, RecommendationResponse
from api.services.menu import enrich_menu

MIN_BUDGET = 200.0


def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """
    Build a weeks menu and shopping cart.
    """
    if request.presupuesto is not None and request.presupuesto < MIN_BUDGET:
        return RecommendationResponse(
            menu_semanal=enrich_menu(EMPTY_MENU),
            carrito_final=OVER_BUDGET_CART,
            mensaje=(
                f"Con ${request.presupuesto:.0f} no alcanza para una semana "
                f"completa. El mínimo estimado es ${MIN_BUDGET:.0f}."
            ),
        )

    return RecommendationResponse(
        menu_semanal=enrich_menu(FAKE_MENU),
        carrito_final=FAKE_CART,
        mensaje=None,
    )
