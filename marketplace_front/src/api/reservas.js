import clienteApi from './axios'

export const cotizar = (datos) => clienteApi.post('/reservas/cotizacion/', datos)
export const reservar = (datos) => clienteApi.post('/reservas/', datos)
export const misReservas = (estado) => clienteApi.get('/reservas/', { params: { estado } })
export const reservasRecibidas = (filtros) => clienteApi.get('/reservas/recibidas/', { params: filtros })
export const obtenerReserva = (id) => clienteApi.get(`/reservas/${id}/`)
export const cancelarReserva = (id, motivo) => clienteApi.post(`/reservas/${id}/cancelacion/`, { motivo })

export async function descargarFactura(id, numero) {
  const { data } = await clienteApi.get(`/reservas/${id}/factura/pdf/`, { responseType: 'blob' })
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(data)
  enlace.download = `${numero}.pdf`
  enlace.click()
  URL.revokeObjectURL(enlace.href)
}
