import clienteApi from './axios'

export const obtenerCsrf = () => clienteApi.get('/csrf/')

export const registrar = (datos) => clienteApi.post('/auth/registro/', datos)
export const verificarCorreo = (datos) => clienteApi.post('/auth/verificar/', datos)
export const reenviarCodigo = (datos) => clienteApi.post('/auth/reenviar-codigo/', datos)

export const ingresar = (correo_o_usuario, contrasena) =>
  clienteApi.post('/auth/ingresar/', { correo_o_usuario, contrasena })
export const salir = () => clienteApi.post('/auth/salir/')

export const recuperar = (datos) => clienteApi.post('/auth/recuperar/', datos)
export const restablecer = (datos) => clienteApi.post('/auth/restablecer/', datos)
export const solicitarReactivacion = (datos) => clienteApi.post('/auth/solicitar-reactivacion/', datos)
export const reactivar = (datos) => clienteApi.post('/auth/reactivar/', datos)

export const obtenerPerfil = () => clienteApi.get('/usuarios/perfil/')
export const actualizarPerfil = (datos) => clienteApi.put('/usuarios/perfil/', datos)
export const cambiarContrasena = (datos) => clienteApi.post('/usuarios/perfil/contrasena/', datos)
export const desactivarCuenta = () => clienteApi.patch('/usuarios/perfil/desactivar/')

export const listarUsuarios = () => clienteApi.get('/administracion/usuarios/')
export const restringirUsuario = (id, motivo) =>
  clienteApi.post(`/administracion/usuarios/${id}/restringir/`, { motivo })
export const liberarUsuario = (id) =>
  clienteApi.post(`/administracion/usuarios/${id}/liberar/`)