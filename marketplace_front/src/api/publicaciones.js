import clienteApi from './axios'

export const listarPublicaciones = (filtros) => clienteApi.get('/publicaciones/', { params: filtros })
export const obtenerPublicacion = (id) => clienteApi.get(`/publicaciones/${id}/`)
export const misPublicaciones = () => clienteApi.get('/publicaciones/mias/')
export const obtenerCalendario = (id) => clienteApi.get(`/publicaciones/${id}/calendario/`)
export const urlImagen = (id, imagen) => `${clienteApi.defaults.baseURL}/publicaciones/${id}/imagenes/${imagen}/archivo/`
