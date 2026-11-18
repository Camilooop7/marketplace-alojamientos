import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import ReporteAnfitrion, { FiltroPeriodo } from '../components/Reporte'
import { descargarMiReporte, descargarReporteAnfitrion, miReporte, reporteAnfitrion } from '../api/reportes'
import { extraerErrores } from '../utils/errores'

const activos = (filtros) => Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor))

export default function Reportes() {
  const { id } = useParams()
  const ubicacion = useLocation()
  const [filtros, setFiltros] = useState((ubicacion.state && ubicacion.state.filtros) || { desde: '', hasta: '' })
  const [reporte, setReporte] = useState(null)
  const [error, setError] = useState('')
  const [descargando, setDescargando] = useState(false)

  useEffect(() => {
    if (filtros.desde && filtros.hasta && filtros.desde > filtros.hasta) return
    const consulta = id ? reporteAnfitrion(id, activos(filtros)) : miReporte(activos(filtros))
    consulta
      .then(({ data }) => {
        setReporte(data)
        setError('')
      })
      .catch((fallo) => setError(extraerErrores(fallo).mensaje))
  }, [id, filtros])

  async function descargar() {
    setDescargando(true)
    try {
      if (id) await descargarReporteAnfitrion(id, activos(filtros), reporte.anfitrion.usuario)
      else await descargarMiReporte(activos(filtros), reporte.anfitrion.usuario)
    } catch (fallo) {
      setError(extraerErrores(fallo).mensaje)
    } finally {
      setDescargando(false)
    }
  }

  return (
    <section className="pagina">
      <div className="contenedor">
        <div className="cabecera">
          {id && <Link className="reporte-volver" to="/administracion/reportes" state={{ filtros }}>
            ← Todos los anfitriones</Link>}
          <p className="etiqueta-seccion">{id ? 'Reporte de anfitrión' : 'Mis reportes'}</p>
          <h1>{reporte ? reporte.anfitrion.nombre : 'Reportes'}</h1>
          <p>{id ? reporte && `${reporte.anfitrion.usuario} · ${reporte.anfitrion.correo}`
            : 'Ingresos, huéspedes y estancias de tus alojamientos.'}</p>
          <FiltroPeriodo filtros={filtros} onCambio={setFiltros}>
            <Boton chico cargando={descargando} disabled={!reporte} onClick={descargar}>Descargar PDF</Boton>
          </FiltroPeriodo>
        </div>

        <Alerta>{filtros.desde && filtros.hasta && filtros.desde > filtros.hasta
          ? 'La fecha inicial no puede ser posterior a la final.' : error}</Alerta>

        {reporte ? <ReporteAnfitrion reporte={reporte} /> : !error && <p className="cargando">Cargando reporte...</p>}
      </div>
    </section>
  )
}
