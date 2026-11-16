from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.csrf, name='csrf'),
    path('auth/registro/', views.RegistroView.as_view(), name='registro'),
    path('auth/verificar/', views.VerificarCorreoView.as_view(), name='verificar_correo'),
    path('auth/reenviar-codigo/', views.ReenviarCodigoView.as_view(), name='reenviar_codigo'),
    path('auth/ingresar/', views.IngresarView.as_view(), name='ingresar'),
    path('auth/salir/', views.SalirView.as_view(), name='salir'),
    path('auth/recuperar/', views.RecuperarView.as_view(), name='recuperar'),
    path('auth/restablecer/', views.RestablecerView.as_view(), name='restablecer'),
    path('auth/reactivar/', views.ReactivarView.as_view(), name='reactivar'),
    path('usuarios/perfil/', views.PerfilView.as_view(), name='perfil'),
    path('usuarios/perfil/desactivar/', views.DesactivarCuentaView.as_view(), name='desactivar_cuenta'),
    path('administracion/usuarios/', views.UsuarioListaAdminView.as_view(), name='admin_usuarios'),
    path('administracion/usuarios/<int:pk>/restringir/', views.RestringirUsuarioView.as_view(),
         name='restringir_usuario'),
    path('administracion/usuarios/<int:pk>/liberar/', views.LiberarUsuarioView.as_view(),
         name='liberar_usuario'),
]