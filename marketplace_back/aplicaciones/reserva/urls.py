from django.urls import path
from . import views

urlpatterns = [
    path('reservas/', views.ReservaListaView.as_view(), name='reservas'),
    path('reservas/cotizacion/', views.CotizacionView.as_view(), name='cotizacion'),
    path('reservas/recibidas/', views.ReservasRecibidasView.as_view(), name='reservas_recibidas'),
    path('reservas/<int:pk>/', views.ReservaDetalleView.as_view(), name='reserva'),
    path('reservas/<int:pk>/cancelacion/', views.CancelacionView.as_view(), name='cancelacion'),
    path('reservas/<int:pk>/factura/', views.FacturaView.as_view(), name='factura'),
    path('reservas/<int:pk>/factura/pdf/', views.FacturaPdfView.as_view(), name='factura_pdf'),
    path('publicaciones/<int:pk>/calendario/', views.CalendarioView.as_view(), name='calendario'),
]
