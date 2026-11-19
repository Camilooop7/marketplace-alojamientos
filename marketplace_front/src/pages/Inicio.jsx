import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Alerta from '../components/Alerta'
import TarjetaAlojamiento from '../components/TarjetaAlojamiento'
import { listarPublicaciones } from '../api/publicaciones'
import { useAuth } from '../context/contextoAuth'

export default function Inicio() {
  const { usuario } = useAuth()
  const ubicacion = useLocation()
  const aviso = ubicacion.state && ubicacion.state.aviso
  const [lista, setLista] = useState([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    listarPublicaciones({})
      .then(({ data }) => setLista(data))
      .catch(() => setLista([]))
      .finally(() => setCargando(false))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="contenedor">
          <Alerta>{aviso}</Alerta>
          <h1>Un lugar donde quedarse.</h1>
          <p>
            Marketplace de alojamientos. Crea tu cuenta como huésped o anfitrión y empieza.
          </p>
          <div className="acciones">
            <Link className="boton boton-fantasma" to="/alojamientos">Ver alojamientos</Link>
            {usuario ? (
              <Link className="boton boton-primario" to="/perfil">Ir a mi perfil</Link>
            ) : (
              <>
                <Link className="boton boton-primario" to="/registro">Crear cuenta</Link>
                <Link className="boton boton-fantasma" to="/ingreso">Ingresar</Link>
              </>
            )}
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="contenedor">
          <p className="etiqueta-seccion">Alojamientos</p>
          <h2>Elige dónde quedarte.</h2>
          {cargando ? (
            <p className="cargando">Cargando alojamientos...</p>
          ) : lista.length === 0 ? (
            <p className="vacio">Todavía no hay alojamientos publicados.</p>
          ) : (
            <div className="rejilla">
              {lista.map((item) => <TarjetaAlojamiento key={item.id} item={item} />)}
            </div>
          )}
        </div>
      </section>

      <section className="seccion seccion-hueso">
        <div className="contenedor">
          <p className="etiqueta-seccion">Roles</p>
          <h2>¿Cómo quieres usarlo?</h2>
          <div className="tarjetas">
            <article className="tarjeta tarjeta-bruma">
              <div>
                <p className="etiqueta-seccion">Huésped</p>
                <h3>Quiero hospedarme</h3>
              </div>
              <p>Crea tu cuenta para reservar alojamientos.</p>
              {!usuario && <Link className="boton boton-fantasma" to="/registro">Registrarme</Link>}
            </article>
            <article className="tarjeta tarjeta-pino">
              <div>
                <p className="etiqueta-seccion">Anfitrión</p>
                <h3>Quiero publicar</h3>
              </div>
              <p>Crea tu cuenta para ofrecer tus alojamientos.</p>
              {!usuario && <Link className="boton boton-primario" to="/registro">Registrarme</Link>}
            </article>
          </div>
        </div>
      </section>
    </>
  )
}