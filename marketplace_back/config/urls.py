from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def estado(request):
    return JsonResponse({'mensaje': 'API del Marketplace de Alojamientos en funcionamiento.'})


urlpatterns = [
    path('', estado, name='estado'),
    path('admin/', admin.site.urls),
    path('api/', include('aplicaciones.gestion_usuario.urls')),
    path('api/', include('aplicaciones.publicacion.urls')),
    path('api/', include('aplicaciones.reserva.urls')),
]