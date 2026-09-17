import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "raw_data/precio_por_producto.csv"

OUTPUT_PATH = (
    "raw_data/"
    "precio_por_producto_bilingual.csv"
)


# ============================================================
# SPANISH -> ENGLISH PRODUCT DICTIONARY
# ============================================================

PRODUCT_TRANSLATIONS = {
    "Aceite": "Oil",
    "Aguacate": "Avocado",
    "Ajo": "Garlic",
    "Ajonjoli": "Sesame",
    "Alcachofa": "Artichoke",
    "Alimento Preparado para Ninos": "Prepared Baby Food",
    "Alimentos Preparados": "Prepared Foods",
    "Almeja": "Clam",
    "Alubia": "White Bean",
    "Amaranto": "Amaranth",
    "Apio": "Celery",
    "Arroz": "Rice",
    "Atun": "Tuna",
    "Avena": "Oats",
    "Azucar": "Sugar",
    "Bagre": "Catfish",
    "Bandera": "Bandera Fish",
    "Barras de Avena": "Oat Bars",
    "Barras de Cereal": "Cereal Bars",
    "Barrita de Surimi o Barrita de Surimi Cangre":
        "Surimi or Imitation Crab Stick",
    "Basa": "Basa Fish",
    "Besugo": "Sea Bream",
    "Betabel": "Beet",
    "Blanco del Nilo": "Nile Perch",
    "Brocoli": "Broccoli",
    "Cafe Soluble": "Instant Coffee",
    "Cafe Tostado y Molido": "Roasted Ground Coffee",
    "Calabaza": "Squash",
    "Calamar": "Squid",
    "Callo de Almeja": "Clam Meat",
    "Callo de Hacha": "Scallop",
    "Camaron": "Shrimp",
    "Carne Cerdo": "Pork",
    "Carne Pavo": "Turkey",
    "Carne Pollo": "Chicken",
    "Carne Res": "Beef",
    "Carne Ternera": "Veal",
    "Carpa": "Carp",
    "Cazon": "Dogfish",
    "Cebolla": "Onion",
    "Cereales": "Cereals",
    "Champinones": "Mushrooms",
    "Charal": "Charal Fish",
    "Chayote": "Chayote",
    "Chia": "Chia Seeds",
    "Chicharo": "Pea",
    "Chicharos": "Peas",
    "Chicharos en Lata": "Canned Peas",
    "Chile Fresco": "Fresh Chili Pepper",
    "Chile Seco": "Dried Chili Pepper",
    "Chiles": "Chili Peppers",
    "Chorizo": "Chorizo",
    "Chucumite": "Chucumite Fish",
    "Cintilla": "Cutlassfish",
    "Ciruela": "Plum",
    "Clavo": "Clove",
    "Coctel de Frutas en Almibar":
        "Fruit Cocktail in Syrup",
    "Col": "Cabbage",
    "Combinado Primavera": "Spring Vegetable Mix",
    "Comino": "Cumin",
    "Concentrado de Pollo": "Chicken Bouillon",
    "Crema": "Cream",
    "Crema Batida": "Whipped Cream",
    "Curcuma": "Turmeric",
    "Curvina": "Croaker Fish",
    "Durazno": "Peach",
    "Duraznos en Almibar": "Peaches in Syrup",
    "Ejote": "Green Bean",
    "Elote": "Corn",
    "Empanizadores": "Bread Crumbs",
    "Floretes de Brocoli": "Broccoli Florets",
    "Formula Lactea": "Milk Formula",
    "Fresa": "Strawberry",
    "Frijol": "Bean",
    "Frijoles": "Beans",
    "Galletas Dulces": "Sweet Cookies",
    "Galletas Populares": "Cookies",
    "Galletas Saladas": "Crackers",
    "Garbanzo": "Chickpea",
    "Granada": "Pomegranate",
    "Granola": "Granola",
    "Granos de Elote": "Corn Kernels",
    "Grasa Comestible": "Cooking Fat",
    "Guanabana": "Soursop",
    "Guarnicion de Verduras": "Vegetable Side Dish",
    "Guayaba": "Guava",
    "Gurrubata": "Gurrubata Fish",
    "Haba": "Fava Bean",
    "Harina Hot Cakes": "Pancake Mix",
    "Harina de Arroz": "Rice Flour",
    "Harina de Maiz": "Corn Flour",
    "Harina de Trigo": "Wheat Flour",
    "Helado": "Ice Cream",
    "Hojas de Laurel": "Bay Leaves",
    "Huachinango": "Red Snapper",
    "Huevo": "Egg",
    "Jaiba": "Crab",
    "Jaibon": "Jaibon Crab",
    "Jamon": "Ham",
    "Jitomate": "Tomato",
    "Jurel": "Horse Mackerel",
    "Kiwi": "Kiwi",
    "Langosta": "Lobster",
    "Langostino": "Prawn",
    "Leche Condensada": "Condensed Milk",
    "Leche Evaporada": "Evaporated Milk",
    "Leche Pasteurizada": "Pasteurized Milk",
    "Leche Ultrapasteurizada": "UHT Milk",
    "Leche en Polvo": "Powdered Milk",
    "Lenguado": "Sole",
    "Lenteja": "Lentil",
    "Limon": "Lemon",
    "Linaza": "Flaxseed",
    "Lisa": "Mullet",
    "Lobina": "Sea Bass",
    "Maiz Palomero": "Popcorn Kernels",
    "Maiz Pozolero": "Pozole Corn",
    "Mamey": "Mamey",
    "Mandarina": "Mandarin",
    "Mango": "Mango",
    "Manteca de Cerdo": "Lard",
    "Mantequilla": "Butter",
    "Manzana": "Apple",
    "Margarina": "Margarine",
    "Mayonesa": "Mayonnaise",
    "Melon": "Melon",
    "Merluza": "Hake",
    "Mermelada": "Jam",
    "Mero": "Grouper",
    "Mezcla California": "California Vegetable Mix",
    "Mezcla Campesina": "Country Vegetable Mix",
    "Mojarra": "Tilapia",
    "Mole Rojo en Pasta": "Red Mole Paste",
    "Mortadela": "Bologna",
    "Mostaza": "Mustard",
    "Naranja": "Orange",
    "Nopal": "Nopal Cactus",
    "Nuez": "Walnut",
    "Oregano": "Oregano",
    "Pampano": "Pompano",
    "Pan Dulce": "Sweet Bread",
    "Pan de Caja": "Sandwich Bread",
    "Papa": "Potato",
    "Papaya": "Papaya",
    "Pargo": "Snapper",
    "Pasta para Sopa": "Soup Pasta",
    "Pastel Pimiento": "Pimento Loaf",
    "Pastelillos y Pan Dulce Empaquetado":
        "Packaged Pastries and Sweet Bread",
    "Pechuga de Pavo": "Turkey Breast",
    "Pepino": "Cucumber",
    "Pera": "Pear",
    "Peron": "Apple",
    "Peto": "Wahoo Fish",
    "Pimienta": "Pepper",
    "Pimiento": "Bell Pepper",
    "Pina": "Pineapple",
    "Pina en Almibar": "Pineapple in Syrup",
    "Platano": "Banana",
    "Polvo P/hornear": "Baking Powder",
    "Producto Lacteo": "Dairy Product",
    "Pulpo": "Octopus",
    "Pure de Tomate": "Tomato Puree",
    "Queso Americano": "American Cheese",
    "Queso Canasto": "Basket Cheese",
    "Queso Chihuahua": "Chihuahua Cheese",
    "Queso Cotija": "Cotija Cheese",
    "Queso Doble Crema": "Double Cream Cheese",
    "Queso Fresco": "Fresh Cheese",
    "Queso Manchego": "Manchego Cheese",
    "Queso Oaxaca": "Oaxaca Cheese",
    "Queso Panela": "Panela Cheese",
    "Queso Sierra": "Sierra Cheese",
    "Queso de Puerco": "Head Cheese",
    "Robalito": "Small Snook",
    "Robalo": "Snook",
    "Rubia": "Rubia Fish",
    "Sal Molida de Mesa": "Table Salt",
    "Sal de Mar": "Sea Salt",
    "Salchicha": "Sausage",
    "Salmon": "Salmon",
    "Salsa Catsup": "Ketchup",
    "Salsa Picante y Similares": "Hot Sauce",
    "Sandia": "Watermelon",
    "Sardina": "Sardine",
    "Semilla de Girasol": "Sunflower Seed",
    "Sierra": "Spanish Mackerel",
    "Soya": "Soy",
    "Sustituto de Azucar": "Sugar Substitute",
    "Te": "Tea",
    "Tilapia": "Tilapia",
    "Tocino Ahumado": "Smoked Bacon",
    "Tomate": "Tomato",
    "Toronja": "Grapefruit",
    "Tortilla de Harina de Trigo":
        "Wheat Flour Tortilla",
    "Tortilla de Maiz": "Corn Tortilla",
    "Tostadas de Maiz": "Corn Tostadas",
    "Trucha": "Trout",
    "Tuna": "Prickly Pear",
    "Uva": "Grape",
    "Verdolaga": "Purslane",
    "Villajaiba": "Villajaiba Crab",
    "Vinagre": "Vinegar",
    "Yoghurt": "Yogurt",
    "Zanahoria": "Carrot",
}


# ============================================================
# LOAD CSV
# ============================================================

print("Loading price dataset...")

df = pd.read_csv(
    INPUT_PATH
)

print(
    f"Rows: {len(df)}"
)


# ============================================================
# REMOVE OLD INDEX COLUMN
# ============================================================

if "Unnamed: 0" in df.columns:
    df = df.drop(
        columns=["Unnamed: 0"]
    )


# ============================================================
# CREATE ENGLISH PRODUCT COLUMN
# ============================================================

df["producto ing"] = (
    df["producto"]
    .map(PRODUCT_TRANSLATIONS)
)


# ============================================================
# VALIDATE TRANSLATIONS
# ============================================================

missing = df[
    df["producto ing"].isna()
]["producto"].tolist()


if missing:

    print(
        "\nWARNING: Products without translation:"
    )

    for product in missing:
        print(
            "-",
            product,
        )

else:

    print(
        "\n✅ All products translated."
    )


# ============================================================
# REORDER COLUMNS
# ============================================================

desired_columns = [
    "producto",
    "producto ing",
    "unit",
    "min_price",
    "max_price",
    "average_price",
]


df = df[
    desired_columns
]


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print(
    "\n" + "=" * 60
)

print(
    "NUTRIPLAN — BILINGUAL PRICE DATASET"
)

print(
    "=" * 60
)

print(
    f"Rows: {len(df)}"
)

print(
    f"Translated products: "
    f"{df['producto ing'].notna().sum()}"
)

print(
    f"Missing translations: "
    f"{df['producto ing'].isna().sum()}"
)

print(
    f"Saved to: {OUTPUT_PATH}"
)


print(
    "\n=== SAMPLE ==="
)

print(
    df.head(20)
    .to_string(index=False)
)
