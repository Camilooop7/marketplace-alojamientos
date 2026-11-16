import { Navigate, Route, Routes } from 'react-router-dom'
import Estructura from './components/Estructura'
import { RutaProtegida, RutaPublica } from './components/Rutas'
import Inicio from './pages/Inicio'
import Registro from './pages/Registro'
import VerificarCorreo from './pages/VerificarCorreo'
import Ingreso from './pages/Ingreso'
import Recuperar from './pages/Recuperar'
import Restablecer from './pages/Restablecer'
import Reactivar from './pages/Reactivar'
import Perfil from './pages/Perfil'
import AdminUsuarios from './pages/AdminUsuarios'
import Alojamientos from './pages/Alojamientos'
import Alojamiento from './pages/Alojamiento'
import MisReservas from './pages/MisReservas'
import ReservasRecibidas from './pages/ReservasRecibidas'
import MisPublicaciones from './pages/MisPublicaciones'

function App() {
  return (
    <Routes>
      <Route element={<Estructura />}>
        <Route path="/" element={<Inicio />} />
        <Route path="/perfil" element={<RutaProtegida><Perfil /></RutaProtegida>} />
        <Route path="/alojamientos" element={<Alojamientos />} />
        <Route path="/alojamientos/:id" element={<Alojamiento />} />
        <Route path="/mis-reservas" element={<RutaProtegida rol="Huesped"><MisReservas /></RutaProtegida>} />
        <Route path="/reservas-recibidas"
          element={<RutaProtegida rol="Anfitrion"><ReservasRecibidas /></RutaProtegida>} />
        <Route path="/mis-publicaciones"
          element={<RutaProtegida rol="Anfitrion"><MisPublicaciones /></RutaProtegida>} />
        <Route
          path="/administracion/usuarios"
          element={<RutaProtegida soloAdministrador><AdminUsuarios /></RutaProtegida>}
        />
      </Route>

      <Route path="/registro" element={<RutaPublica><Registro /></RutaPublica>} />
      <Route path="/ingreso" element={<RutaPublica><Ingreso /></RutaPublica>} />
      <Route path="/verificar" element={<VerificarCorreo />} />
      <Route path="/recuperar" element={<Recuperar />} />
      <Route path="/restablecer" element={<Restablecer />} />
      <Route path="/reactivar" element={<Reactivar />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App