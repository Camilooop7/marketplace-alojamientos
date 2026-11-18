export const ETIQUETA_ESTADO = {
  ACTIVO: 'Activo',
  INACTIVO: 'Inactivo',
  RESTRINGIDO: 'Restringido',
}

export const ETIQUETA_RESERVA = {
  PENDIENTE_PAGO: 'Pendiente de pago',
  CONFIRMADA: 'Confirmada',
  CANCELADA: 'Cancelada',
  COMPLETADA: 'Completada',
}

export const ETIQUETA_PUBLICACION = {
  BORRADOR: 'Borrador',
  PENDIENTE_REVISION: 'Pendiente de revisión',
  ACTIVA: 'Activa',
  PAUSADA: 'Pausada',
  BLOQUEADA: 'Bloqueada',
}

export const TIPOS_ALOJAMIENTO = {
  CASA: 'Casa',
  APARTAMENTO: 'Apartamento',
  HABITACION: 'Habitación',
  CABANA: 'Cabaña',
}

export function fechaLegible(texto) {
  if (!texto) return ''
  const fecha = /^\d{4}-\d{2}-\d{2}$/.test(texto) ? new Date(`${texto}T00:00:00`) : new Date(texto)
  return fecha.toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

export function pesos(valor) {
  return Number(valor || 0).toLocaleString('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  })
}

export function hoyIso(dias = 0) {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() + dias)
  return fecha.toLocaleDateString('en-CA')
}

export const entero = (valor) => Number(valor || 0).toLocaleString('es-CO')

export const decimal = (valor) =>
  Number(valor || 0).toLocaleString('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
