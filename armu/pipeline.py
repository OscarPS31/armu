from armu.pricing import (
    load_profeco_prices,
    find_profeco_price,
)


class NutriPlanMatcher:
    """
    Public interface for ingredient -> PROFECO matching.

    The PROFECO dataset is loaded once when the matcher
    is created, so multiple searches are faster.
    """

    def __init__(
        self,
        profeco_path=None,
    ):
        print("Loading PROFECO dataset...")

        self.prices = load_profeco_prices(
            profeco_path
        )

        print("PROFECO dataset ready.")


    def match_ingredient(
        self,
        ingredient,
    ):
        """
        Match one ingredient against PROFECO.
        """

        return find_profeco_price(
            ingredient,
            self.prices,
        )


    def match_ingredients(
        self,
        ingredients,
    ):
        """
        Match multiple ingredients against PROFECO.
        """

        results = []

        for ingredient in ingredients:

            result = self.match_ingredient(
                ingredient
            )

            results.append(
                result
            )

        return results


    def build_shopping_cart(
        self,
        ingredients,
    ):
        """
        Match multiple ingredients and calculate
        an estimated shopping cart total.

        Current MVP assumption:
        one median-priced product/package
        per unique normalized ingredient.
        """

        results = self.match_ingredients(
            ingredients
        )

        unique_products = {}

        unmatched = []


        for result in results:

            if result["status"] != "MATCHED":

                unmatched.append(
                    result
                )

                continue


            normalized = result[
                "normalized"
            ]


            if normalized not in unique_products:

                unique_products[
                    normalized
                ] = result


        cart = list(
            unique_products.values()
        )


        total = sum(
            item["median_price"]
            for item in cart
        )


        return {
            "cart": cart,

            "total": round(
                total,
                2,
            ),

            "matched_products": len(
                cart
            ),

            "unmatched_products": len(
                unmatched
            ),

            "unmatched": unmatched,
        }
