import { Link } from 'react-router-dom'
import { useAuth } from '../context/contextoAuth'

export default function Inicio() {
  const { usuario } = useAuth()

  return (
    <>
      <section className="hero">
        <div className="contenedor">
          <h1>Un lugar donde quedarse.</h1>
          <p>
            Marketplace de alojamientos. Crea tu cuenta como huésped o anfitrión y empieza.
          </p>
          <div className="acciones">
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