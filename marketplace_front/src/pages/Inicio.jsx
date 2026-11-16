import { Link } from 'react-router-dom'
import { useAuth } from '../context/contextoAuth'

const PASOS = [
  ['01', 'Crea tu cuenta', 'Elige si eres huésped o anfitrión y completa tus datos.'],
  ['02', 'Verifica tu correo', 'Te enviamos un código de 6 dígitos para activar la cuenta.'],
  ['03', 'Ingresa', 'Entra con tu correo o con tu nombre de usuario.'],
  ['04', 'Administra tu perfil', 'Actualiza tus datos o desactiva tu cuenta cuando quieras.'],
]

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

      <section className="seccion">
        <div className="contenedor">
          <p className="etiqueta-seccion">Cómo empezar</p>
          <h2>Cuatro pasos.</h2>
          <ol className="lista-pasos">
            {PASOS.map(([numero, titulo, texto]) => (
              <li key={numero}>
                <span className="numero">{numero}</span>
                <div>
                  <h3>{titulo}</h3>
                  <p>{texto}</p>
                </div>
              </li>
            ))}
          </ol>
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