MAX_COMPARE = 4  # Nombre maximum de produits à comparer


class CompareService:
    @staticmethod
    def get_compare(request):
        return request.session.get('compare', [])

    @staticmethod
    def add_to_compare(request, product_id):
        compare = request.session.get('compare', [])
        product_id = int(product_id)

        if product_id in compare:
            return True, 'Ce produit est déjà dans votre comparaison.'

        if len(compare) >= MAX_COMPARE:
            return False, f'Vous pouvez comparer au maximum {MAX_COMPARE} produits à la fois.'

        compare.append(product_id)
        request.session['compare'] = compare
        request.session.modified = True
        return True, 'Produit ajouté à la comparaison.'

    @staticmethod
    def remove_from_compare(request, product_id):
        compare = request.session.get('compare', [])
        product_id = int(product_id)

        if product_id in compare:
            compare.remove(product_id)

        request.session['compare'] = compare
        request.session.modified = True

    @staticmethod
    def clear_compare(request):
        request.session.pop('compare', None)
        request.session.modified = True
