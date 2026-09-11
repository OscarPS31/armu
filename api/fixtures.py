from api.schemas import Cart, CartItem

FAKE_MENU= {
    'monday': [407021],
    'tuesday': [216687],
    'wednesday': [26732],
    'thursday': [501882],
    'friday': [88498],
    'saturday': [349505],
    'sunday': [333860]
}



FAKE_CART = Cart(
    items=[
        CartItem(ingrediente="pollo", cantidad=2, costo=159.80),
        CartItem(ingrediente="arroz", cantidad=1, costo=34.50),
    ],
    costo_total=194.30,
    dentro_de_presupuesto=True,
    ingredientes_sin_precio=["oregano"],
    items_retirados=["salmon"],
)

EMPTY_MENU = {day: [] for day in FAKE_MENU}

OVER_BUDGET_CART = Cart(
    costo_total=812.40,
    dentro_de_presupuesto=False,
)
