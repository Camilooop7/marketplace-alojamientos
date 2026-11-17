import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import Campo from '../components/Campo'
import Galeria from '../components/Galeria'
import { useAuth } from '../context/contextoAuth'
import { obtenerCalendario, obtenerPublicacion } from '../api/publicaciones'
import { cotizar, reservar } from '../api/reservas'
import { extraerErrores, sinErrores } from '../utils/errores'
import { TIPOS_ALOJAMIENTO, fechaLegible, hoyIso, pesos } from '../utils/estados'

function nuevaClave() {
  return crypto.randomUUID()
}

export default function Alojamiento() {
  const { id } = useParams()
  const navegar = useNavigate()
  const { usuario } = useAuth()
  const [publicacion, setPublicacion] = useState(null)
  const [calendario, setCalendario] = useState({ disponibles: [], reservadas: [] })
  const [errorCarga, setErrorCarga] = useState('')
  const [datos, setDatos] = useState({ fecha_entrada: '', fecha_salida: '', huespedes: '1', servicios: [] })
  const [cotizacion, setCotizacion] = useState(null)
  const [errores, setErrores] = useState(sinErrores)
  const [enviando, setEnviando] = useState(false)
  const [clave, setClave] = useState(nuevaClave)

  useEffect(() => {
    Promise.all([obtenerPublicacion(id), obtenerCalendario(id)])
      .then(([pub, cal]) => {
        setPublicacion(pub.data)
        setCalendario(cal.data)
      })
      .catch((fallo) => setErrorCarga(extraerErrores(fallo).mensaje))
  }, [id])

  function cambiar(evento) {
    setDatos({ ...datos, [evento.target.name]: evento.target.value })
    setCotizacion(null)
  }

  function alternarServicio(servicioId) {
    const servicios = datos.servicios.includes(servicioId)
      ? datos.servicios.filter((item) => item !== servicioId)
      : [...datos.servicios, servicioId]
    setDatos({ ...datos, servicios })
    setCotizacion(null)
  }

  const solicitud = { ...datos, publicacion: Number(id), huespedes: Number(datos.huespedes) || 0 }

  async function pedirCotizacion(evento) {
    evento.preventDefault()
    setEnviando(true)
    setErrores(sinErrores)
    try {
      const { data } = await cotizar(solicitud)
      setCotizacion(data)
      setClave(nuevaClave())
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
    } finally {
      setEnviando(false)
    }
  }

  async function confirmar() {
    setEnviando(true)
    setErrores(sinErrores)
    try {
      const { data } = await reservar({ ...solicitud, clave_idempotencia: clave })
      navegar('/mis-reservas', { state: { aviso: data.mensaje, nueva: data.reserva.id } })
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
      setCotizacion(null)
    } finally {
      setEnviando(false)
    }
  }

  if (errorCarga) {
    return (
      <section className="pagina"><div className="contenedor">
        <Alerta>{errorCarga}</Alerta>
        <Link to="/alojamientos">Volver a los alojamientos</Link>
      </div></section>
    )
  }
  if (!publicacion) return <p className="cargando">Cargando alojamiento...</p>

  const campos = errores.campos

  return (
    <section className="pagina">
      <div className="contenedor">
        <p className="etiqueta-seccion">{TIPOS_ALOJAMIENTO[publicacion.tipo]} · {publicacion.ciudad}</p>
        <h1>{publicacion.titulo}</h1>
        <Galeria publicacion={publicacion} />

        <div className="detalle">
          <div>
            <p className="descripcion">{publicacion.descripcion}</p>
            <div className="panel">
              <dl className="datos">
                <div><dt>Ubicación</dt><dd>{publicacion.direccion}, {publicacion.ciudad}</dd></div>
                <div><dt>Capacidad</dt><dd>{publicacion.capacidad} huéspedes</dd></div>
                <div><dt>Precio por noche</dt><dd>{pesos(publicacion.precio_noche)}</dd></div>
                <div><dt>Limpieza</dt><dd>{pesos(publicacion.tarifa_limpieza)}</dd></div>
                {publicacion.descuento_porcentaje > 0 && (
                  <div><dt>Descuento</dt>
                    <dd>{publicacion.descuento_porcentaje} % desde {publicacion.noches_descuento} noches</dd></div>
                )}
                <div><dt>Anfitrión</dt><dd>{publicacion.anfitrion}</dd></div>
              </dl>
            </div>

            <h2>Calendario</h2>
            <div className="calendario">
              <div>
                <p className="etiqueta-grupo">Fechas disponibles</p>
                {calendario.disponibles.length === 0 ? <p>Sin fechas disponibles por ahora.</p> : (
                  <ul>{calendario.disponibles.map((p) => (
                    <li key={p.inicio}>Del {fechaLegible(p.inicio)} al {fechaLegible(p.fin)}</li>
                  ))}</ul>
                )}
              </div>
              <div>
                <p className="etiqueta-grupo">Fechas ocupadas</p>
                {calendario.reservadas.length === 0 ? <p>Ninguna.</p> : (
                  <ul>{calendario.reservadas.map((r) => (
                    <li key={r.inicio}>Del {fechaLegible(r.inicio)} al {fechaLegible(r.fin)}</li>
                  ))}</ul>
                )}
              </div>
            </div>
          </div>

          <aside className="panel caja-reserva">
            <h2>Cotiza tu estancia</h2>
            <form onSubmit={pedirCotizacion} noValidate>
              <Alerta>{errores.mensaje}</Alerta>
              <div className="fila-2">
                <Campo etiqueta="Entrada" nombre="fecha_entrada" tipo="date" valor={datos.fecha_entrada}
                  onCambio={cambiar} error={campos.fecha_entrada} min={hoyIso()} />
                <Campo etiqueta="Salida" nombre="fecha_salida" tipo="date" valor={datos.fecha_salida}
                  onCambio={cambiar} error={campos.fecha_salida} min={datos.fecha_entrada || hoyIso(1)} />
              </div>
              <Campo etiqueta="Huéspedes" nombre="huespedes" tipo="number" valor={datos.huespedes}
                onCambio={cambiar} error={campos.huespedes} min="1" max={publicacion.capacidad} />
              {publicacion.servicios.length > 0 && (
                <>
                  <p className="etiqueta-grupo">Servicios adicionales</p>
                  {publicacion.servicios.map((servicio) => (
                    <label key={servicio.id} className="casilla">
                      <input type="checkbox" checked={datos.servicios.includes(servicio.id)}
                        onChange={() => alternarServicio(servicio.id)} />
                      {servicio.nombre} ({pesos(servicio.precio)})
                    </label>
                  ))}
                  {campos.servicios && <p className="campo-error">{campos.servicios}</p>}
                </>
              )}
              <Boton type="submit" variante="fantasma" bloque cargando={enviando && !cotizacion}>Cotizar</Boton>
            </form>

            {cotizacion && (
              <div className="cotizacion">
                <table>
                  <tbody>
                    <tr><td>{cotizacion.noches} noches x {pesos(cotizacion.precio_noche)}</td>
                      <td>{pesos(cotizacion.precio_base)}</td></tr>
                    {Number(cotizacion.descuento) > 0 && (
                      <tr><td>Descuento</td><td>- {pesos(cotizacion.descuento)}</td></tr>
                    )}
                    <tr><td>Limpieza</td><td>{pesos(cotizacion.tarifa_limpieza)}</td></tr>
                    {cotizacion.servicios.map((s) => (
                      <tr key={s.nombre}><td>{s.nombre}</td><td>{pesos(s.precio)}</td></tr>
                    ))}
                    <tr className="total"><td>Total</td><td>{pesos(cotizacion.total)}</td></tr>
                  </tbody>
                </table>
                {!usuario ? (
                  <Link className="boton boton-primario boton-bloque" to="/ingreso"
                    state={{ desde: `/alojamientos/${id}` }}>Ingresa para reservar</Link>
                ) : usuario.id !== publicacion.anfitrion_id ? (
                  <>
                    <Boton bloque cargando={enviando} onClick={confirmar}>Reservar</Boton>
                    <p className="campo-ayuda">Se generará tu factura. La reserva queda pendiente hasta el pago.</p>
                  </>
                ) : (
                  <p className="campo-ayuda">Esta es tu publicación, no puedes reservarla.</p>
                )}
              </div>
            )}
          </aside>
        </div>
      </div>
    </section>
  )
}
