import {Navigate, useLocation} from 'react-router-dom'
import {useAuth} from '../context/contextoAuth'

function Cargando() {
    return <p className="cargando">Cargando...</p>
}

export function RutaProtegida({children, soloAdministrador = false}) {
    const {usuario, cargando, esAdministrador} = useAuth()
    const ubicacion = useLocation()

    if (cargando) return <Cargando/>
    if (!usuario) {
        return <Navigate to="/ingreso" replace state={{desde: ubicacion.pathname}}/>
    }
    if (soloAdministrador && !esAdministrador) return <Navigate to="/" replace/>
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