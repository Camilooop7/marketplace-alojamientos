import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/contextoAuth'
import Boton from './Boton'

export default function BarraNavegacion() {
  const { usuario, esAdministrador, esHuesped, esAnfitrion, salir } = useAuth()
  const navegar = useNavigate()

  async function cerrarSesion() {
    await salir().catch(() => {})
    navegar('/')
  }

  return (
    <header className="barra">
      <div className="contenedor barra-interior">
        <Link to="/" className="logo">Market<br />place</Link>

        <nav className="barra-enlaces">
          <NavLink to="/alojamientos">Alojamientos</NavLink>
          {(esHuesped || esAnfitrion) && <NavLink to="/mis-reservas">Mis reservas</NavLink>}
          {esAnfitrion && <NavLink to="/mis-publicaciones">Mis publicaciones</NavLink>}
          {esAnfitrion && <NavLink to="/reservas-recibidas">Reservas recibidas</NavLink>}
          {usuario && <NavLink to="/perfil">Mi perfil</NavLink>}
          {esAdministrador && <NavLink to="/administracion/usuarios">Usuarios</NavLink>}
        </nav>

        <div className="barra-acciones">
          {usuario ? (
            <>
              <span className="saludo">Hola, {usuario.nombres}</span>
              <Boton variante="fantasma" chico onClick={cerrarSesion}>Salir</Boton>
            </>
          ) : (
            <>
              <Link className="boton boton-fantasma boton-chico" to="/ingreso">Ingresar</Link>
              <Link className="boton boton-primario boton-chico" to="/registro">Crear cuenta</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}