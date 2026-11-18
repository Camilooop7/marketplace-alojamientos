from django.urls import path
from . import views

urlpatterns = [
    path('reportes/mio/', views.MiReporteView.as_view(), name='mi_reporte'),
    path('reportes/mio/pdf/', views.MiReportePdfView.as_view(), name='mi_reporte_pdf'),
    path('reportes/anfitriones/', views.ReporteGeneralView.as_view(), name='reporte_general'),
    path('reportes/anfitriones/pdf/', views.ReporteGeneralPdfView.as_view(), name='reporte_general_pdf'),
    path('reportes/anfitriones/<int:pk>/', views.ReporteAnfitrionView.as_view(), name='reporte_anfitrion'),
    path('reportes/anfitriones/<int:pk>/pdf/', views.ReporteAnfitrionPdfView.as_view(),
         name='reporte_anfitrion_pdf'),
]
