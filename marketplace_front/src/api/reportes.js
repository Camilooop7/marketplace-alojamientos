import clienteApi from './axios'

export const miReporte = (filtros) => clienteApi.get('/reportes/mio/', { params: filtros })
export const reporteGeneral = (filtros) => clienteApi.get('/reportes/anfitriones/', { params: filtros })
export const reporteAnfitrion = (id, filtros) => clienteApi.get(`/reportes/anfitriones/${id}/`, { params: filtros })

async function descargar(ruta, filtros, nombre) {
  try {
    const { data } = await clienteApi.get(ruta, { params: filtros, responseType: 'blob' })
    const enlace = document.createElement('a')
    enlace.href = URL.createObjectURL(data)
    enlace.download = `${[nombre, filtros.desde, filtros.hasta].filter(Boolean).join('-')}.pdf`
    enlace.click()
    URL.revokeObjectURL(enlace.href)
  } catch (fallo) {
    if (fallo.response && fallo.response.data instanceof Blob) {
      fallo.response.data = await fallo.response.data.text().then(JSON.parse).catch(() => null)
    }
    throw fallo
  }
}

export const descargarMiReporte = (filtros, usuario) =>
  descargar('/reportes/mio/pdf/', filtros, `reporte-${usuario}`)
export const descargarReporteGeneral = (filtros) =>
  descargar('/reportes/anfitriones/pdf/', filtros, 'reporte-anfitriones')
export const descargarReporteAnfitrion = (id, filtros, usuario) =>
  descargar(`/reportes/anfitriones/${id}/pdf/`, filtros, `reporte-${usuario}`)
