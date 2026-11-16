import clienteApi from './axios'

export const listarPublicaciones = (filtros) => clienteApi.get('/publicaciones/', { params: filtros })
export const obtenerPublicacion = (id) => clienteApi.get(`/publicaciones/${id}/`)
export const misPublicaciones = () => clienteApi.get('/publicaciones/mias/')
export const crearPublicacion = (datos) => clienteApi.post('/publicaciones/', datos)
export const actualizarPublicacion = (id, datos) => clienteApi.put(`/publicaciones/${id}/`, datos)

export const listarDisponibilidad = (id) => clienteApi.get(`/publicaciones/${id}/disponibilidad/`)
export const agregarDisponibilidad = (id, datos) => clienteApi.post(`/publicaciones/${id}/disponibilidad/`, datos)
export const eliminarDisponibilidad = (id, periodo) =>
  clienteApi.delete(`/publicaciones/${id}/disponibilidad/${periodo}/`)
export const obtenerCalendario = (id) => clienteApi.get(`/publicaciones/${id}/calendario/`)

export const subirImagen = (id, archivo) => {
  const formulario = new FormData()
  formulario.append('imagen', archivo)
  return clienteApi.post(`/publicaciones/${id}/imagenes/`, formulario)
}
export const eliminarImagen = (id, imagen) => clienteApi.delete(`/publicaciones/${id}/imagenes/${imagen}/`)
export const urlImagen = (id, imagen) => `${clienteApi.defaults.baseURL}/publicaciones/${id}/imagenes/${imagen}/archivo/`
