import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import {
  Estados, FiltroPeriodo, GraficoMeses, Indicadores, Seccion,
} from '../components/Reporte'
import { descargarReporteAnfitrion, descargarReporteGeneral, reporteGeneral } from '../api/reportes'
import { extraerErrores } from '../utils/errores'
import { entero, pesos } from '../utils/estados'

const activos = (filtros) => Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor))

export default function AdminReportes() {
  const ubicacion = useLocation()
  const [filtros, setFiltros] = useState((ubicacion.state && ubicacion.state.filtros) || { desde: '', hasta: '' })
  const [reporte, setReporte] = useState(null)
  const [error, setError] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [descargando, setDescargando] = useState(null)
  const invertidas = Boolean(filtros.desde && filtros.hasta && filtros.desde > filtros.hasta)

  useEffect(() => {
    if (invertidas) return
    reporteGeneral(activos(filtros))
      .then(({ data }) => {
        setReporte(data)
        setError('')
      })
      .catch((fallo) => setError(extraerErrores(fallo).mensaje))
  }, [filtros, invertidas])

  async function descargar(clave, accion) {
    setDescargando(clave)
    try {
      await accion()
    } catch (fallo) {
      setError(extraerErrores(fallo).mensaje)
    } finally {
      setDescargando(null)
    }
  }

  const texto = busqueda.trim().toLowerCase()
  const visibles = reporte ? reporte.anfitriones.filter((fila) =>
    `${fila.nombre} ${fila.usuario} ${fila.correo}`.toLowerCase().includes(texto)) : []

  return (
    <section className="pagina">
      <div className="contenedor">
        <div className="cabecera">
          <p className="etiqueta-seccion">Administración</p>
          <h1>Reportes</h1>
          <p>Ingresos, reservas y huéspedes de cada anfitrión de la plataforma.</p>
          <FiltroPeriodo filtros={filtros} onCambio={setFiltros}>
            <Boton chico cargando={descargando === 'general'} disabled={!reporte}
              onClick={() => descargar('general', () => descargarReporteGeneral(activos(filtros)))}>
              Descargar reporte general
            </Boton>
          </FiltroPeriodo>
        </div>

        <Alerta>{invertidas ? 'La fecha inicial no puede ser posterior a la final.' : error}</Alerta>

        {!reporte ? !error && <p className="cargando">Cargando reportes...</p> : (
          <>
            <Indicadores resumen={reporte.resumen} general />
            <Estados estados={reporte.estados} />

            <Seccion titulo="Ingresos por mes" nota="Valor facturado según el mes de entrada de cada reserva.">
              <GraficoMeses meses={reporte.meses} />
            </Seccion>

            <Seccion titulo="Anfitriones" nota="Ordenados por valor facturado en el periodo.">
              <div className="barra-herramientas">
                <div className="entrada">
                  <input type="search" placeholder="Buscar por nombre, usuario o correo" value={busqueda}
                    onChange={(evento) => setBusqueda(evento.target.value)} />
                </div>
              </div>
              {visibles.length === 0 ? <p className="vacio">No hay anfitriones que coincidan.</p> : (
                <div className="tabla-contenedor">
                  <table>
                    <thead>
                      <tr><th>Anfitrión</th><th className="numero">Alojamientos</th><th className="numero">Reservas</th>
                        <th className="numero">Noches</th><th className="numero">Huéspedes</th>
                        <th className="numero">Ingresos</th><th>Acciones</th></tr>
                    </thead>
                    <tbody>
                      {visibles.map((fila) => (
                        <tr key={fila.id}>
                          <td>{fila.nombre}<span className="motivo">{fila.usuario} · {fila.correo}</span></td>
                          <td className="numero">{entero(fila.alojamientos)}</td>
                          <td className="numero">{entero(fila.reservas)}
                            {fila.canceladas > 0 && (
                              <span className="motivo">{entero(fila.canceladas)} canc.</span>)}</td>
                          <td className="numero">{entero(fila.noches)}</td>
                          <td className="numero">{entero(fila.huespedes)}</td>
                          <td className="numero">{pesos(fila.ingresos)}</td>
                          <td>
                            <div className="botones">
                              <Link className="boton boton-fantasma boton-chico" to={`/administracion/reportes/${fila.id}`}
                                state={{ filtros }}>Ver reporte</Link>
                              <Boton variante="fantasma" chico cargando={descargando === fila.id}
                                onClick={() => descargar(fila.id,
                                  () => descargarReporteAnfitrion(fila.id, activos(filtros), fila.usuario))}>
                                PDF
                              </Boton>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Seccion>
          </>
        )}
      </div>
    </section>
  )
}
