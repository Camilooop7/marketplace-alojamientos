import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import { FilaReserva, FiltroEstado, Historial } from '../components/TablaReservas'
import { cancelarReserva, descargarFactura, misReservas, obtenerReserva } from '../api/reservas'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function MisReservas() {
  const ubicacion = useLocation()
  const [reservas, setReservas] = useState([])
  const [estado, setEstado] = useState('')
  const [cargando, setCargando] = useState(true)
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState((ubicacion.state && ubicacion.state.aviso) || '')
  const [abierta, setAbierta] = useState(null)
  const [cancelando, setCancelando] = useState(null)
  const [motivo, setMotivo] = useState('')

  const cargar = useCallback(() => {
    misReservas(estado || undefined)
      .then(({ data }) => setReservas(data))
      .catch((fallo) => setErrores(extraerErrores(fallo)))
      .finally(() => setCargando(false))
  }, [estado])

  useEffect(() => { cargar() }, [cargar])

  async function bajarFactura(reserva) {
    try {
      await descargarFactura(reserva.id, reserva.factura)
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
    }
  }

  async function verDetalle(id) {
    if (abierta && abierta.id === id) return setAbierta(null)
    try {
      const { data } = await obtenerReserva(id)
      setAbierta(data)
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
    }
  }

  function iniciarCancelacion(reserva) {
    setErrores(sinErrores)
    setAviso('')
    setCancelando({ id: reserva.id })
    setMotivo('')
  }

  async function confirmarCancelacion(evento) {
    evento.preventDefault()
    setErrores(sinErrores)
    try {
      const { data } = await cancelarReserva(cancelando.id, motivo)
      setAviso(data.mensaje)
      setCancelando(null)
      setAbierta(null)
      cargar()
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
    }
  }

  return (
    <section className="pagina">
      <div className="contenedor">
        <h1>Mis reservas</h1>
        <Alerta tipo="exito">{aviso}</Alerta>
        <Alerta>{errores.mensaje}</Alerta>

        <div className="barra-herramientas">
          <FiltroEstado valor={estado} onCambio={setEstado} />
          <Link className="boton boton-fantasma" to="/alojamientos">Buscar alojamientos</Link>
        </div>

        {cargando ? <p className="cargando">Cargando reservas...</p> : reservas.length === 0 ? (
          <p className="vacio">No tienes reservas{estado && ' con ese estado'}.</p>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Código</th><th>Alojamiento</th><th>Fechas</th><th>Total</th><th>Estado</th><th>Acciones</th></tr>
              </thead>
              <tbody>
                {reservas.map((reserva) => (
                  <FilaReserva key={reserva.id} reserva={reserva}>
                    <div className="botones">
                      <Boton variante="fantasma" chico onClick={() => verDetalle(reserva.id)}>Detalle</Boton>
                      <Boton variante="fantasma" chico onClick={() => bajarFactura(reserva)}>Factura PDF</Boton>
                      {['PENDIENTE_PAGO', 'CONFIRMADA'].includes(reserva.estado) && (
                        <Boton variante="peligro" chico onClick={() => iniciarCancelacion(reserva)}>Cancelar</Boton>
                      )}
                    </div>
                    {cancelando && cancelando.id === reserva.id && (
                      <form className="form-linea" onSubmit={confirmarCancelacion}>
                        <input placeholder="Motivo de la cancelación" value={motivo}
                          onChange={(evento) => setMotivo(evento.target.value)} autoFocus />
                        {errores.campos.motivo && <span className="campo-error">{errores.campos.motivo}</span>}
                        <div className="botones">
                          <Boton type="submit" variante="peligro" chico>Confirmar cancelación</Boton>
                          <Boton variante="fantasma" chico onClick={() => setCancelando(null)}>Volver</Boton>
                        </div>
                      </form>
                    )}
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
