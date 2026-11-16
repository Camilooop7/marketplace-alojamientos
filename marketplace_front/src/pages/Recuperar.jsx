import { useState } from 'react'
import { Link } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { recuperar } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function Recuperar() {
  const [datos, cambiar] = useFormulario({ correo: '' })
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState('')
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    setAviso('')
    try {
      const { data } = await recuperar(datos)
      setAviso(data.mensaje)
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  return (
    <DisenoAuth
      titulo="Recupera tu contraseña"
      subtitulo="Te enviaremos un enlace a tu correo para crear una contraseña nueva."
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