import { Link } from 'react-router-dom'
import { ETIQUETA_RESERVA, decimal, entero, fechaLegible, pesos } from '../utils/estados'

function abreviado(valor) {
  if (valor >= 1000000) return `$ ${decimal(valor / 1000000)} M`
  if (valor >= 1000) return `$ ${entero(Math.round(valor / 1000))} mil`
  return pesos(valor)
}

function escala(maximo) {
  if (maximo <= 0) return 1
  const bruto = (maximo * 1.08) / 3
  const potencia = 10 ** Math.floor(Math.log10(bruto))
  const factor = [1, 2, 2.5, 5, 10].find((opcion) => opcion * potencia >= bruto)
  return factor * potencia * 3
}

export function FiltroPeriodo({ filtros, onCambio, children }) {
  return (
    <div className="barra-herramientas">
      <label className="filtro-fecha">Desde
        <input type="date" value={filtros.desde} max={filtros.hasta || undefined}
          onChange={(evento) => onCambio({ ...filtros, desde: evento.target.value })} />
      </label>
      <label className="filtro-fecha">Hasta
        <input type="date" value={filtros.hasta} min={filtros.desde || undefined}
          onChange={(evento) => onCambio({ ...filtros, hasta: evento.target.value })} />
      </label>
      {(filtros.desde || filtros.hasta) && (
        <button type="button" className="boton-texto" onClick={() => onCambio({ desde: '', hasta: '' })}>
          Ver todo el historial
        </button>
      )}
      <div className="reporte-acciones">{children}</div>
    </div>
  )
}

function Indicador({ etiqueta, valor, destacado = false }) {
  return (
    <div className={destacado ? 'indicador indicador-destacado' : 'indicador'}>
      <p className="indicador-etiqueta">{etiqueta}</p>
      <p className="indicador-valor">{valor}</p>
    </div>
  )
}

export function Indicadores({ resumen, general = false }) {
  return (
    <div className="indicadores">
      <Indicador destacado etiqueta="Ingresos facturados" valor={pesos(resumen.ingresos)} />
      <Indicador etiqueta="Confirmados" valor={pesos(resumen.ingresos_confirmados)} />
      <Indicador etiqueta="Por cobrar" valor={pesos(resumen.ingresos_pendientes)} />
      <Indicador etiqueta="Reservas" valor={entero(resumen.reservas)} />
      {general && <Indicador etiqueta="Anfitriones" valor={entero(resumen.anfitriones)} />}
      <Indicador etiqueta="Noches reservadas" valor={entero(resumen.noches)} />
      <Indicador etiqueta="Huéspedes alojados" valor={entero(resumen.huespedes)} />
      {!general && <Indicador etiqueta="Alojamientos" valor={entero(resumen.alojamientos)} />}
      <Indicador etiqueta="Canceladas" valor={entero(resumen.canceladas)} />
    </div>
  )
}

export function Estados({ estados }) {
  return (
    <div className="reporte-estados">
      {estados.map((dato) => (
        <span key={dato.estado} className={`insignia insignia-reserva-${dato.estado.toLowerCase()}`}>
          {dato.etiqueta} · {entero(dato.cantidad)}
        </span>
      ))}
    </div>
  )
}

export function Seccion({ titulo, nota, children }) {
  return (
    <section className="reporte-seccion">
      <h2>{titulo}</h2>
      {nota && <p className="reporte-nota">{nota}</p>}
      {children}
    </section>
  )
}

export function GraficoMeses({ meses }) {
  if (meses.length === 0) return <p className="vacio">No hay reservas en este periodo.</p>
  const maximo = Math.max(...meses.map((mes) => Number(mes.ingresos)))
  const tope = escala(maximo)
  const salto = Math.ceil(meses.length / 12)

  return (
    <div className="grafico">
      <div className="grafico-eje" aria-hidden="true">
        {[3, 2, 1, 0].map((paso) => <span key={paso}>{abreviado((tope * paso) / 3)}</span>)}
      </div>
      <div className="grafico-area">
        <div className="grafico-plano" aria-hidden="true">
          {[1, 2, 3].map((paso) => (
            <span key={paso} className="grafico-guia" style={{ bottom: `${(paso * 100) / 3}%` }} />
          ))}
        </div>
        <div className="grafico-columnas">
          {meses.map((mes, indice) => {
            const valor = Number(mes.ingresos)
            return (
              <div key={mes.mes} className="grafico-columna" tabIndex={0}
                aria-label={`${mes.etiqueta}: ${pesos(valor)}, ${mes.reservas} reservas`}>
                <div className="grafico-barra" style={{ height: `${(valor * 100) / tope}%` }}>
                  {valor === maximo && valor > 0 && <span className="grafico-maximo">{abreviado(valor)}</span>}
                </div>
                <div className="grafico-globo" role="tooltip">
                  <strong>{mes.etiqueta}</strong>
                  <span>{pesos(valor)}</span>
                  <span>{entero(mes.reservas)} reservas · {entero(mes.noches)} noches</span>
                  <span>{entero(mes.huespedes)} huéspedes</span>
                </div>
                <span className="grafico-mes">{indice % salto === 0 ? mes.etiqueta : ''}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function ReporteAnfitrion({ reporte }) {
  const { resumen } = reporte

  return (
    <>
      <Indicadores resumen={resumen} />
      <Estados estados={reporte.estados} />

      <Seccion titulo="Ingresos por mes" nota="Valor facturado según el mes de entrada de cada reserva.">
        <GraficoMeses meses={reporte.meses} />
      </Seccion>

      <Seccion titulo="Rendimiento por alojamiento">
        {reporte.alojamientos.length === 0 ? <p className="vacio">Todavía no hay alojamientos publicados.</p> : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Alojamiento</th><th className="numero">Reservas</th><th className="numero">Noches</th>
                  <th className="numero">Huéspedes</th><th className="numero">Ingresos</th></tr>
              </thead>
              <tbody>
                {reporte.alojamientos.map((fila) => (
                  <tr key={fila.id}>
                    <td><Link to={`/alojamientos/${fila.id}`}>{fila.titulo}</Link>
                      <span className="motivo">{fila.tipo_etiqueta} · {fila.ciudad}</span></td>
                    <td className="numero">{entero(fila.reservas)}
                      {fila.canceladas > 0 && <span className="motivo">{entero(fila.canceladas)} canc.</span>}</td>
                    <td className="numero">{entero(fila.noches)}</td>
                    <td className="numero">{entero(fila.huespedes)}</td>
                    <td className="numero">{pesos(fila.ingresos)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Seccion>

      <Seccion titulo="Quiénes reservan" nota="Huéspedes con reservas vigentes, ordenados por valor facturado.">
        {reporte.clientes.length === 0 ? <p className="vacio">No hay huéspedes con reservas vigentes en este periodo.</p> : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Huésped</th><th className="numero">Reservas</th><th className="numero">Noches</th>
                  <th className="numero">Personas</th><th className="numero">Total</th></tr>
              </thead>
              <tbody>
                {reporte.clientes.map((fila) => (
                  <tr key={fila.id}>
                    <td>{fila.nombre}<span className="motivo">{fila.correo}</span></td>
                    <td className="numero">{entero(fila.reservas)}</td>
                    <td className="numero">{entero(fila.noches)}</td>
                    <td className="numero">{entero(fila.huespedes)}</td>
                    <td className="numero">{pesos(fila.ingresos)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Seccion>

      <Seccion titulo="Detalle de reservas" nota="El total no incluye las reservas canceladas.">
        {reporte.reservas.length === 0 ? <p className="vacio">No hay reservas en este periodo.</p> : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Código</th><th>Huésped</th><th>Alojamiento</th><th>Estancia</th>
                  <th className="numero">Personas</th><th className="numero">Total</th><th>Estado</th></tr>
              </thead>
              <tbody>
                {reporte.reservas.map((fila) => (
                  <tr key={fila.id}>
                    <td>{fila.codigo}</td>
                    <td>{fila.huesped}</td>
                    <td>{fila.alojamiento}<span className="motivo">{fila.tipo}</span></td>
                    <td>{fechaLegible(fila.fecha_entrada)}
                      <span className="motivo">{entero(fila.noches)} noches</span></td>
                    <td className="numero">{entero(fila.huespedes)}</td>
                    <td className="numero">{pesos(fila.total)}</td>
                    <td><span className={`insignia insignia-reserva-${fila.estado.toLowerCase()}`}>
                      {ETIQUETA_RESERVA[fila.estado]}</span></td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr><td colSpan={3}>Total</td><td>{entero(resumen.noches)} noches</td>
                  <td className="numero">{entero(resumen.huespedes)}</td>
                  <td className="numero">{pesos(resumen.ingresos)}</td><td /></tr>
              </tfoot>
            </table>
          </div>
        )}
      </Seccion>
    </>
  )
}
