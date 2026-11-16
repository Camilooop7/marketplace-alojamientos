from django.urls import path
from . import views

urlpatterns = [
    path('publicaciones/', views.PublicacionListaView.as_view(), name='publicaciones'),
    path('publicaciones/mias/', views.MisPublicacionesView.as_view(), name='mis_publicaciones'),
    path('publicaciones/<int:pk>/', views.PublicacionDetalleView.as_view(), name='publicacion'),
    path('publicaciones/<int:pk>/disponibilidad/', views.DisponibilidadView.as_view(),
         name='disponibilidad'),
    path('publicaciones/<int:pk>/disponibilidad/<int:periodo_id>/',
         views.DisponibilidadDetalleView.as_view(), name='disponibilidad_detalle'),
    path('publicaciones/<int:pk>/imagenes/', views.ImagenesView.as_view(), name='imagenes'),
    path('publicaciones/<int:pk>/imagenes/<int:imagen_id>/', views.ImagenDetalleView.as_view(),
         name='imagen'),
    path('publicaciones/<int:pk>/imagenes/<int:imagen_id>/archivo/', views.ImagenArchivoView.as_view(),
         name='imagen_archivo'),
]
