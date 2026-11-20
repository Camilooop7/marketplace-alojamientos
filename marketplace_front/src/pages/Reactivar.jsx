import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { reactivar, solicitarReactivacion } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

function SolicitarEnlace() {
  const ubicacion = useLocation()
  const [datos, cambiar] = useFormulario({ correo: (ubicacion.state && ubicacion.state.correo) || '' })
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState('')
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    setAviso('')
    try {
      const { data } = await solicitarReactivacion(datos)
      setAviso(data.mensaje)
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  return (
    <DisenoAuth
      titulo="Reactiva tu cuenta"
      subtitulo="Te enviaremos un enlace a tu correo para volver a activar tu cuenta."
      pie={<Link to="/ingreso">Volver a ingresar</Link>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta tipo="exito">{aviso}</Alerta>
        <Alerta>{errores.mensaje}</Alerta>

        <Campo etiqueta="Correo electrónico" nombre="correo" tipo="email" valor={datos.correo}
          onCambio={cambiar} error={errores.campos.correo} autoComplete="email" />

        <Boton type="submit" bloque cargando={cargando}>Enviar enlace</Boton>
      </form>
    </DisenoAuth>
  )
}

function ConfirmarReactivacion({ correo, token }) {
  const navegar = useNavigate()
  const [errores, setErrores] = useState(sinErrores)
  const [cargando, setCargando] = useState(false)

  async function confirmar() {
    setCargando(true)
    setErrores(sinErrores)
    try {
      const { data } = await reactivar({ correo, token })
      navegar('/ingreso', { state: { aviso: data.mensaje } })
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  return (
    <DisenoAuth
      titulo="Reactiva tu cuenta"
      subtitulo={`Cuenta: ${correo}`}
      pie={<Link to="/reactivar">Pedir un enlace nuevo</Link>}
    >
      <Alerta>{errores.mensaje}</Alerta>
      <Boton bloque cargando={cargando} onClick={confirmar}>Reactivar cuenta</Boton>
    </DisenoAuth>
  )
}

export default function Reactivar() {
  const [parametros] = useSearchParams()
  const correo = parametros.get('correo') || ''
  const token = parametros.get('token') || ''

  if (correo && token) return <ConfirmarReactivacion correo={correo} token={token} />
  return <SolicitarEnlace />
}
