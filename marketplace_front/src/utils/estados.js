export const ETIQUETA_ESTADO = {
  ACTIVO: 'Activo',
  INACTIVO: 'Inactivo',
  RESTRINGIDO: 'Restringido',
}

export function fechaLegible(texto) {
  if (!texto) return ''
  return new Date(texto).toLocaleDateString('es-CO', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}