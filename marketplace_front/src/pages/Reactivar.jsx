import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { useAuth } from '../context/contextoAuth'
import { reactivar } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function Reactivar() {
  const { establecerUsuario } = useAuth()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const inicial = (ubicacion.state && ubicacion.state.correo_o_usuario) || ''

  const [datos, cambiar] = useFormulario({ correo_o_usuario: inicial, contrasena: '' })
  const [errores, setErrores] = useState(sinErrores)
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    try {
      const { data } = await reactivar(datos)
      establecerUsuario(data.usuario)
      navegar('/perfil', { replace: true })
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  const campos = errores.campos

  return (
    <DisenoAuth
      titulo="Reactiva tu cuenta"
      subtitulo="Confirma tus credenciales para volver a activar tu cuenta."
      pie={<Link to="/ingreso">Volver a ingresar</Link>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta>{errores.mensaje}</Alerta>

        <Campo etiqueta="Correo o nombre de usuario" nombre="correo_o_usuario"
          valor={datos.correo_o_usuario} onCambio={cambiar} error={campos.correo_o_usuario}
          autoComplete="username" />
        <Campo etiqueta="Contraseña" nombre="contrasena" tipo="password" valor={datos.contrasena}
          onCambio={cambiar} error={campos.contrasena} autoComplete="current-password" />

        <Boton type="submit" bloque cargando={cargando}>Reactivar cuenta</Boton>
      </form>
    </DisenoAuth>
  )
}