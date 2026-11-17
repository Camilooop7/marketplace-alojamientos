import {Navigate, useLocation} from 'react-router-dom'
import {useAuth} from '../context/contextoAuth'

function Cargando() {
    return <p className="cargando">Cargando...</p>
}

export function RutaProtegida({children, soloAdministrador = false, rol = null}) {
    const {usuario, cargando, esAdministrador, esHuesped, esAnfitrion} = useAuth()
    const ubicacion = useLocation()

    if (cargando) return <Cargando/>
    if (!usuario) {
        return <Navigate to="/ingreso" replace state={{desde: ubicacion.pathname}}/>
    }
    if (soloAdministrador && !esAdministrador) return <Navigate to="/" replace/>
    if (rol === 'Huesped' && !esHuesped) return <Navigate to="/" replace/>
    if (rol === 'Anfitrion' && !esAnfitrion) return <Navigate to="/" replace/>
    return children
}

export function RutaPublica({children}) {
    const {usuario, cargando} = useAuth()
    const ubicacion = useLocation()

    if (cargando) return <Cargando/>
    if (usuario) {
        return <Navigate to={(ubicacion.state && ubicacion.state.desde) || '/perfil'} replace/>
    }
    return children
}