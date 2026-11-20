import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { useAuth } from '../context/contextoAuth'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function Ingreso() {
  const { ingresar } = useAuth()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const estado = ubicacion.state || {}

  const [datos, cambiar] = useFormulario({ correo_o_usuario: '', contrasena: '' })
  const [errores, setErrores] = useState(sinErrores)
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    try {
      await ingresar(datos.correo_o_usuario, datos.contrasena)
    } catch (error) {
      const detalle = extraerErrores(error)
      if (detalle.datos.requiere_verificacion) {
        navegar('/verificar', { state: { correo: detalle.datos.correo, aviso: detalle.mensaje } })
        return
      }
      setErrores(detalle)
    } finally {
      setCargando(false)
    }
  }

  const campos = errores.campos

  return (
    <DisenoAuth
      titulo="Ingresa"
      subtitulo="Usa tu correo o tu nombre de usuario."
      pie={<>¿No tienes cuenta? <Link to="/registro">Crea una</Link></>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta tipo="exito">{estado.aviso}</Alerta>
        <Alerta>{errores.mensaje}</Alerta>
        {errores.datos.requiere_reactivacion && (
          <Alerta tipo="info">
            <Link to="/reactivar" state={{ correo: errores.datos.correo }}>
              Reactivar mi cuenta
            </Link>
          </Alerta>
        )}

        <Campo etiqueta="Correo o nombre de usuario" nombre="correo_o_usuario"
          valor={datos.correo_o_usuario} onCambio={cambiar} error={campos.correo_o_usuario}
          autoComplete="username" />
        <Campo etiqueta="Contraseña" nombre="contrasena" tipo="password" valor={datos.contrasena}
          onCambio={cambiar} error={campos.contrasena} autoComplete="current-password" />

        <div className="auth-extra">
          <Link to="/recuperar">¿Olvidaste tu contraseña?</Link>
        </div>

        <Boton type="submit" bloque cargando={cargando}>Ingresar</Boton>
      </form>
    </DisenoAuth>
  )
}