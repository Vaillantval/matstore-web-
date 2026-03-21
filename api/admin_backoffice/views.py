from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, F, FloatField, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.admin_backoffice.filters import AdminOrderFilter, AdminProductFilter
from api.admin_backoffice.serializers import (
    AdminCategorySerializer,
    AdminCustomerSerializer,
    AdminOrderSerializer,
    InventoryProductSerializer,
    InventoryUpdateSerializer,
    OrderStatusUpdateSerializer,
    ProductImageUploadSerializer,
)
from api.pagination import StandardResultsPagination
from api.permissions import IsAdminUser
from api.products.serializers import ProductAdminSerializer
from shop.models.Category import Category
from shop.models.Image import Image
from shop.models.Order import Order
from shop.models.Product import Product

User = get_user_model()


# ─── Dashboard ────────────────────────────────────────────────────────────────

class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Dashboard"], summary="Statistiques globales")
    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        orders_today = Order.objects.filter(created_at__date=today)
        revenue_today = orders_today.filter(is_paid=True).aggregate(
            total=Sum("order_cost_ttc")
        )["total"] or 0

        revenue_month = (
            Order.objects.filter(created_at__date__gte=month_start, is_paid=True)
            .aggregate(total=Sum("order_cost_ttc"))["total"] or 0
        )

        new_customers_today = User.objects.filter(
            date_joined__date=today, is_staff=False
        ).count()

        pending_orders = Order.objects.filter(status="pending").count()

        # Top 5 products by quantity sold
        from shop.models.OrderDetail import OrderDetail

        top_products = (
            OrderDetail.objects.values("product_name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        # Revenue last 30 days per day
        thirty_days_ago = today - timedelta(days=29)
        revenue_chart = list(
            Order.objects.filter(
                created_at__date__gte=thirty_days_ago,
                is_paid=True,
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("order_cost_ttc"))
            .order_by("day")
            .values("day", "revenue")
        )
        # Fill missing days with 0
        chart_map = {entry["day"]: round(entry["revenue"], 2) for entry in revenue_chart}
        full_chart = []
        for i in range(30):
            d = thirty_days_ago + timedelta(days=i)
            full_chart.append({"date": d.isoformat(), "revenue": chart_map.get(d, 0)})

        return Response({
            "success": True,
            "data": {
                "orders_today": orders_today.count(),
                "revenue_today": round(revenue_today, 2),
                "revenue_month": round(revenue_month, 2),
                "new_customers_today": new_customers_today,
                "pending_orders": pending_orders,
                "top_products": list(top_products),
                "revenue_last_30_days": full_chart,
            },
        })


# ─── Products ─────────────────────────────────────────────────────────────────

class AdminProductListCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Produits"],
        responses={200: ProductAdminSerializer(many=True)},
        summary="Liste complète des produits",
    )
    def get(self, request):
        filterset = AdminProductFilter(
            request.query_params,
            queryset=Product.objects.prefetch_related("images", "categories").order_by("-created_at"),
        )
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        return paginator.get_paginated_response(ProductAdminSerializer(page, many=True).data)

    @extend_schema(
        tags=["Admin - Produits"],
        request=ProductAdminSerializer,
        responses={201: ProductAdminSerializer},
        summary="Créer un produit",
    )
    def post(self, request):
        serializer = ProductAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(
            {"success": True, "data": ProductAdminSerializer(product).data},
            status=status.HTTP_201_CREATED,
        )


class AdminProductDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Product.objects.prefetch_related("images", "categories").get(pk=pk)
        except Product.DoesNotExist:
            return None

    @extend_schema(tags=["Admin - Produits"], request=ProductAdminSerializer, summary="Modifier un produit")
    def patch(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Produit introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProductAdminSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(tags=["Admin - Produits"], summary="Supprimer un produit")
    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Produit introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductImageUploadView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=["Admin - Produits"],
        request=ProductImageUploadSerializer,
        responses={201: ProductImageUploadSerializer},
        summary="Uploader des images pour un produit",
    )
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Produit introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        images = []
        for f in request.FILES.getlist("images"):
            img = Image.objects.create(product=product, image=f)
            images.append(img)
        return Response(
            {"success": True, "data": ProductImageUploadSerializer(images, many=True).data},
            status=status.HTTP_201_CREATED,
        )


# ─── Orders ───────────────────────────────────────────────────────────────────

class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Commandes"],
        responses={200: AdminOrderSerializer(many=True)},
        summary="Toutes les commandes avec filtres",
    )
    def get(self, request):
        filterset = AdminOrderFilter(
            request.query_params,
            queryset=Order.objects.select_related("author").prefetch_related("order_details").order_by("-created_at"),
        )
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(filterset.qs, request)
        return paginator.get_paginated_response(AdminOrderSerializer(page, many=True).data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Commandes"], summary="Détail complet d'une commande")
    def get(self, request, pk):
        try:
            order = Order.objects.select_related("author").prefetch_related("order_details").get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Commande introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "data": AdminOrderSerializer(order).data})


class AdminOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Commandes"],
        request=OrderStatusUpdateSerializer,
        summary="Changer le statut d'une commande",
        description="Déclenche l'email de mise à jour automatiquement via signal.",
    )
    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Commande introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        tracking = serializer.validated_data.get("tracking_number", "")

        order.status = new_status
        if tracking:
            # Store tracking in billing_address notes if no dedicated field
            order.billing_address = f"{order.billing_address} [TRACKING: {tracking}]"
        order.save()  # triggers pre_save + post_save signals → email sent

        return Response({"success": True, "data": AdminOrderSerializer(order).data})


# ─── Customers ────────────────────────────────────────────────────────────────

class AdminCustomerListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Clients"], summary="Liste des clients")
    def get(self, request):
        search = request.query_params.get("search", "")
        qs = User.objects.filter(is_staff=False).order_by("-date_joined")
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(AdminCustomerSerializer(page, many=True).data)


class AdminCustomerDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Clients"], summary="Profil client + historique commandes")
    def get(self, request, pk):
        try:
            customer = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Client introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        orders = Order.objects.filter(author=customer).order_by("-created_at")[:20]
        from api.orders.serializers import OrderSerializer
        return Response({
            "success": True,
            "data": {
                "customer": AdminCustomerSerializer(customer).data,
                "recent_orders": OrderSerializer(orders, many=True).data,
            },
        })

    @extend_schema(tags=["Admin - Clients"], request=AdminCustomerSerializer, summary="Modifier un client")
    def patch(self, request, pk):
        try:
            customer = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Client introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdminCustomerSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


# ─── Categories ───────────────────────────────────────────────────────────────

class AdminCategoryListCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Catégories"], summary="Liste des catégories")
    def get(self, request):
        cats = Category.objects.annotate(product_count=Count("product")).order_by("name")
        return Response({"success": True, "data": AdminCategorySerializer(cats, many=True).data})

    @extend_schema(tags=["Admin - Catégories"], request=AdminCategorySerializer, summary="Créer une catégorie")
    def post(self, request):
        serializer = AdminCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cat = serializer.save()
        return Response(
            {"success": True, "data": AdminCategorySerializer(cat).data},
            status=status.HTTP_201_CREATED,
        )


class AdminCategoryDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    @extend_schema(tags=["Admin - Catégories"], request=AdminCategorySerializer, summary="Modifier une catégorie")
    def patch(self, request, pk):
        cat = self.get_object(pk)
        if not cat:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Catégorie introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AdminCategorySerializer(cat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(tags=["Admin - Catégories"], summary="Supprimer une catégorie")
    def delete(self, request, pk):
        cat = self.get_object(pk)
        if not cat:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Catégorie introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        cat.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Inventory ────────────────────────────────────────────────────────────────

class AdminInventoryListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Inventaire"],
        summary="Produits avec stock faible (< 10)",
        parameters=[OpenApiParameter("threshold", int, description="Seuil de stock (défaut: 10)")],
    )
    def get(self, request):
        threshold = int(request.query_params.get("threshold", 10))
        products = Product.objects.filter(stock__lte=threshold).order_by("stock")
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(products, request)
        return paginator.get_paginated_response(InventoryProductSerializer(page, many=True).data)


class AdminInventoryUpdateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Inventaire"],
        request=InventoryUpdateSerializer,
        summary="Mettre à jour le stock d'un produit",
    )
    def patch(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Produit introuvable."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = InventoryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product.stock = serializer.validated_data["stock"]
        if "is_available" in serializer.validated_data:
            product.is_available = serializer.validated_data["is_available"]
        product.save(update_fields=["stock", "is_available"])

        return Response({"success": True, "data": InventoryProductSerializer(product).data})


# ─── Reports ──────────────────────────────────────────────────────────────────

class AdminSalesReportView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Admin - Rapports"],
        summary="Rapport des ventes par période",
        parameters=[
            OpenApiParameter("period", str, description="daily | weekly | monthly"),
            OpenApiParameter("start", str, description="Date début YYYY-MM-DD"),
            OpenApiParameter("end", str, description="Date fin YYYY-MM-DD"),
        ],
    )
    def get(self, request):
        from django.db.models.functions import TruncDay

        period = request.query_params.get("period", "daily")
        start_str = request.query_params.get("start")
        end_str = request.query_params.get("end")

        try:
            start = date.fromisoformat(start_str) if start_str else (date.today() - timedelta(days=30))
            end = date.fromisoformat(end_str) if end_str else date.today()
        except ValueError:
            return Response(
                {"success": False, "error": {"code": "INVALID_DATE", "message": "Format de date invalide. Utiliser YYYY-MM-DD."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Order.objects.filter(created_at__date__gte=start, created_at__date__lte=end, is_paid=True)

        trunc_map = {"daily": TruncDate, "weekly": TruncWeek, "monthly": TruncMonth}
        TruncFn = trunc_map.get(period, TruncDate)

        data = list(
            qs.annotate(period=TruncFn("created_at"))
            .values("period")
            .annotate(
                revenue=Sum("order_cost_ttc"),
                order_count=Count("id"),
            )
            .order_by("period")
        )

        total = qs.aggregate(
            total_revenue=Sum("order_cost_ttc"),
            total_orders=Count("id"),
        )

        return Response({
            "success": True,
            "data": {
                "period": period,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "breakdown": data,
                "total_revenue": round(total["total_revenue"] or 0, 2),
                "total_orders": total["total_orders"] or 0,
            },
        })


class AdminProductsReportView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Rapports"], summary="Produits les plus vendus")
    def get(self, request):
        from shop.models.OrderDetail import OrderDetail

        limit = int(request.query_params.get("limit", 20))
        top = list(
            OrderDetail.objects.values("product_name")
            .annotate(
                total_qty=Sum("quantity"),
                total_revenue=Sum("sub_total_ttc"),
            )
            .order_by("-total_qty")[:limit]
        )
        return Response({"success": True, "data": top})


class AdminCustomersReportView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(tags=["Admin - Rapports"], summary="Meilleurs clients")
    def get(self, request):
        limit = int(request.query_params.get("limit", 20))
        top = list(
            Order.objects.filter(is_paid=True)
            .values("author__id", "author__username", "author__email",
                    "author__first_name", "author__last_name")
            .annotate(
                order_count=Count("id"),
                total_spent=Sum("order_cost_ttc"),
            )
            .order_by("-total_spent")[:limit]
        )
        return Response({"success": True, "data": top})
