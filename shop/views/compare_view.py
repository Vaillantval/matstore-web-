from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from shop.models import Product
from shop.services.compare_service import CompareService


def compare_detail(request):
    compare_ids = CompareService.get_compare(request)
    compares = []
    if compare_ids:
        compares = list(
            Product.objects
            .prefetch_related('images', 'categories')
            .filter(pk__in=compare_ids)
        )
    return render(request, 'shop/compare.html', {'compares': compares})


@require_POST
def add_to_compare(request, product_id):
    get_object_or_404(Product, pk=product_id)
    success, message = CompareService.add_to_compare(request, product_id)
    compare_count = len(CompareService.get_compare(request))
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': success,
            'msg_type': 'success' if success else 'warning',
            'message': message,
            'compare_count': compare_count,
        })
    return redirect('compare')


@require_POST
def remove_from_compare(request, product_id):
    CompareService.remove_from_compare(request, product_id)
    compare_count = len(CompareService.get_compare(request))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'compare_count': compare_count})
    return redirect('compare')
