import { useCallback, useEffect, useState } from 'react'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import { FilaReserva, FiltroEstado, Historial } from '../components/TablaReservas'
import { descargarFactura, obtenerReserva, reservasRecibidas } from '../api/reservas'
import { extraerErrores } from '../utils/errores'

export default function ReservasRecibidas() {
  const [reservas, setReservas] = useState([])
  const [filtros, setFiltros] = useState({ estado: '', desde: '', hasta: '' })
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')
  const [abierta, setAbierta] = useState(null)

  const cargar = useCallback(() => {
    const activos = Object.fromEntries(Object.entries(filtros).filter(([, valor]) => valor))
    reservasRecibidas(activos)
      .then(({ data }) => setReservas(data))
      .catch((fallo) => setError(extraerErrores(fallo).mensaje))
      .finally(() => setCargando(false))
  }, [filtros])

  useEffect(() => { cargar() }, [cargar])

  async function verDetalle(id) {
    if (abierta && abierta.id === id) return setAbierta(null)
    try {
      setAbierta((await obtenerReserva(id)).data)
    } catch (fallo) {
      setError(extraerErrores(fallo).mensaje)
    }
  }

  async function bajarFactura(reserva) {
    try {
      await descargarFactura(reserva.id, reserva.factura)
    } catch (fallo) {
      setError(extraerErrores(fallo).mensaje)
    }
  }

  return (
    <section className="pagina">
      <div className="contenedor">
        <h1>Reservas recibidas</h1>
        <Alerta>{error}</Alerta>

        <div className="barra-herramientas">
          <FiltroEstado valor={filtros.estado} onCambio={(estado) => setFiltros({ ...filtros, estado })} />
          <label className="filtro-fecha">Desde
            <input type="date" value={filtros.desde}
              onChange={(evento) => setFiltros({ ...filtros, desde: evento.target.value })} />
          </label>
          <label className="filtro-fecha">Hasta
            <input type="date" value={filtros.hasta}
              onChange={(evento) => setFiltros({ ...filtros, hasta: evento.target.value })} />
          </label>
        </div>

        {cargando ? <p className="cargando">Cargando reservas...</p> : reservas.length === 0 ? (
          <p className="vacio">No hay reservas que cumplan esos filtros.</p>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Código</th><th>Alojamiento</th><th>Fechas</th><th>Total</th><th>Estado</th><th>Acciones</th></tr>
              </thead>
              <tbody>
                {reservas.map((reserva) => (
                  <FilaReserva key={reserva.id} reserva={reserva} mostrarHuesped>
                    <div className="botones">
                      <Boton variante="fantasma" chico onClick={() => verDetalle(reserva.id)}>Detalle</Boton>
                      <Boton variante="fantasma" chico onClick={() => bajarFactura(reserva)}>Factura PDF</Boton>
                    </div>
                    {abierta && abierta.id === reserva.id && <Historial reserva={abierta} />}
                  </FilaReserva>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
