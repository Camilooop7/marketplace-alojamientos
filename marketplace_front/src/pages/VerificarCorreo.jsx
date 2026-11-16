import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { reenviarCodigo, verificarCorreo } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

export default function VerificarCorreo() {
  const ubicacion = useLocation()
  const navegar = useNavigate()
  const estado = ubicacion.state || {}

  const [datos, cambiar] = useFormulario({ correo: estado.correo || '', codigo: '' })
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState(estado.aviso || '')
  const [cargando, setCargando] = useState(false)
  const [espera, setEspera] = useState(estado.reciente ? 60 : 0)

  useEffect(() => {
    if (espera <= 0) return undefined
    const temporizador = setTimeout(() => setEspera((segundos) => segundos - 1), 1000)
    return () => clearTimeout(temporizador)
  }, [espera])

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    setAviso('')
    try {
      const { data } = await verificarCorreo(datos)
      navegar('/ingreso', { state: { aviso: data.mensaje } })
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  async function reenviar() {
    setErrores(sinErrores)
    setAviso('')
    try {
      const { data } = await reenviarCodigo({ correo: datos.correo })
      setAviso(data.mensaje)
      setEspera(60)
    } catch (error) {
      setErrores(extraerErrores(error))
    }
  }

  const campos = errores.campos

  return (
    <DisenoAuth
      titulo="Verifica tu correo"
      subtitulo="Escribe el código de 6 dígitos que te enviamos. Vence en 15 minutos."
      pie={<>¿Ya verificaste? <Link to="/ingreso">Ingresa</Link></>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta tipo="info">{aviso}</Alerta>
        <Alerta>{errores.mensaje}</Alerta>

        <Campo etiqueta="Correo electrónico" nombre="correo" tipo="email" valor={datos.correo}
          onCambio={cambiar} error={campos.correo} autoComplete="email" />
        <Campo etiqueta="Código de verificación" nombre="codigo" valor={datos.codigo}
          onCambio={cambiar} error={campos.codigo} inputMode="numeric" maxLength={6}
          autoComplete="one-time-code" placeholder="000000" />

        <Boton type="submit" bloque cargando={cargando}>Verificar</Boton>
      </form>

      <p className="auth-pie">
        ¿No te llegó?{' '}
        <button type="button" className="boton-texto" onClick={reenviar} disabled={espera > 0}>
          {espera > 0 ? `Reenviar código (${espera} s)` : 'Reenviar código'}
        </button>
      </p>
    </DisenoAuth>
  )
}