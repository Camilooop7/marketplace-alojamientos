export default function Boton({
  variante = 'primario',
  cargando = false,
  bloque = false,
  chico = false,
  disabled = false,
  type = 'button',
  children,
}) {
  const clases = ['boton', `boton-${variante}`, bloque && 'boton-bloque', chico && 'boton-chico']
    .filter(Boolean)
    .join(' ')

  return (
    <button type={type} className={clases} disabled={cargando || disabled}>
      {cargando ? 'Procesando...' : children}
    </button>
  )
}