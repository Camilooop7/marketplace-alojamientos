import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import DisenoAuth from '../components/DisenoAuth'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { registrar } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'

const ROLES = [
  { valor: 'Huesped', titulo: 'Huésped', texto: 'Quiero reservar alojamientos.' },
  { valor: 'Anfitrion', titulo: 'Anfitrión', texto: 'Quiero publicar mis alojamientos.' },
]

export default function Registro() {
  const navegar = useNavigate()
  const [datos, cambiar] = useFormulario({
    nombre_usuario: '',
    nombres: '',
    apellidos: '',
    correo: '',
    telefono: '',
    rol: 'Huesped',
    contrasena: '',
    confirmar_contrasena: '',
  })
  const [errores, setErrores] = useState(sinErrores)
  const [cargando, setCargando] = useState(false)

  async function enviar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    try {
      const { data } = await registrar(datos)
      navegar('/verificar', {
        state: { correo: data.correo, aviso: data.mensaje, reciente: data.correo_enviado },
      })
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  const campos = errores.campos

  return (
    <DisenoAuth
      titulo="Crea tu cuenta"
      subtitulo="Te enviaremos un código a tu correo para activarla."
      pie={<>¿Ya tienes cuenta? <Link to="/ingreso">Ingresa</Link></>}
    >
      <form onSubmit={enviar} noValidate>
        <Alerta>{errores.mensaje}</Alerta>

        <p className="etiqueta-grupo">¿Cómo vas a usar la plataforma?</p>
        <div className="opciones">
          {ROLES.map((rol) => (
            <label key={rol.valor} className={`opcion ${datos.rol === rol.valor ? 'activa' : ''}`}>
              <input
                type="radio"
                name="rol"
                value={rol.valor}
                checked={datos.rol === rol.valor}
                onChange={cambiar}
              />
              <strong>{rol.titulo}</strong>
              <span>{rol.texto}</span>
            </label>
          ))}
        </div>
        {campos.rol && <p className="campo-error">{campos.rol}</p>}

        <div className="fila-2" style={{ marginTop: 16 }}>
          <Campo etiqueta="Nombres" nombre="nombres" valor={datos.nombres} onCambio={cambiar}
            error={campos.nombres} autoComplete="given-name" />
          <Campo etiqueta="Apellidos" nombre="apellidos" valor={datos.apellidos} onCambio={cambiar}
            error={campos.apellidos} autoComplete="family-name" />
        </div>
        <Campo etiqueta="Nombre de usuario" nombre="nombre_usuario" valor={datos.nombre_usuario}
          onCambio={cambiar} error={campos.nombre_usuario} autoComplete="username"
          ayuda="Letras sin tilde, números, punto, guion o guion bajo. Mínimo 4." />
        <Campo etiqueta="Correo electrónico" nombre="correo" tipo="email" valor={datos.correo}
          onCambio={cambiar} error={campos.correo} autoComplete="email" />
        <Campo etiqueta="Teléfono (opcional)" nombre="telefono" tipo="tel" valor={datos.telefono}
          onCambio={cambiar} error={campos.telefono} autoComplete="tel" inputMode="numeric"
          ayuda="Solo números, entre 7 y 15 dígitos." />
        <Campo etiqueta="Contraseña" nombre="contrasena" tipo="password" valor={datos.contrasena}
          onCambio={cambiar} error={campos.contrasena} autoComplete="new-password"
          ayuda="8 a 64 caracteres con mayúscula, minúscula, número y símbolo." />
        <Campo etiqueta="Confirmar contraseña" nombre="confirmar_contrasena" tipo="password"
          valor={datos.confirmar_contrasena} onCambio={cambiar}
          error={campos.confirmar_contrasena} autoComplete="new-password" />

        <Boton type="submit" bloque cargando={cargando}>Crear cuenta</Boton>
      </form>
    </DisenoAuth>
  )
}