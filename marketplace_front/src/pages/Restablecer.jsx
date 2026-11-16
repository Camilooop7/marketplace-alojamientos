import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { restablecer } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function Restablecer() {
  const [parametros] = useSearchParams()
  const navegar = useNavigate()
  const correo = parametros.get('correo') || ''
  const token = parametros.get('token') || ''

  const [datos, cambiar] = useFormulario({ contrasena: '', confirmar_contrasena: '' })
  const [errores, setErrores] = useState(sinErrores)
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    try {
      const { data } = await restablecer({ correo, token, ...datos })
      navegar('/ingreso', { state: { aviso: data.mensaje } })
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  const campos = errores.campos

  if (!correo || !token) {
    return (
      <DisenoAuth titulo="Enlace incompleto" pie={<Link to="/recuperar">Pedir un enlace nuevo</Link>}>
        <Alerta>Este enlace no es válido. Pide uno nuevo desde la recuperación de contraseña.</Alerta>
      </DisenoAuth>
    )
  }

  return (
    <DisenoAuth
      titulo="Nueva contraseña"
      subtitulo={`Cuenta: ${correo}`}
      pie={<Link to="/ingreso">Volver a ingresar</Link>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta>{errores.mensaje}</Alerta>
        {campos.token && <Alerta>{campos.token}</Alerta>}

        <Campo etiqueta="Contraseña nueva" nombre="contrasena" tipo="password" valor={datos.contrasena}
          onCambio={cambiar} error={campos.contrasena} autoComplete="new-password"
          ayuda="8 a 64 caracteres con mayúscula, minúscula, número y símbolo." />
        <Campo etiqueta="Confirmar contraseña" nombre="confirmar_contrasena" tipo="password"
          valor={datos.confirmar_contrasena} onCambio={cambiar}
          error={campos.confirmar_contrasena} autoComplete="new-password" />

        <Boton type="submit" bloque cargando={cargando}>Guardar contraseña</Boton>
      </form>
    </DisenoAuth>
  )
}