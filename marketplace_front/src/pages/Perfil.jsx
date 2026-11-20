import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Campo from '../components/Campo'
import Boton from '../components/Boton'
import Alerta from '../components/Alerta'
import useFormulario from '../hooks/useFormulario'
import { useAuth } from '../context/contextoAuth'
import { actualizarPerfil, cambiarContrasena, desactivarCuenta, obtenerCsrf } from '../api/usuarios'
import { extraerErrores, sinErrores } from '../utils/errores'
import { ETIQUETA_ESTADO, fechaLegible } from '../utils/estados'

export default function Perfil() {
  const { usuario, establecerUsuario } = useAuth()
  const navegar = useNavigate()

  const [datos, cambiar] = useFormulario({
    nombres: usuario.nombres,
    apellidos: usuario.apellidos,
    telefono: usuario.telefono || '',
  })
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState('')
  const [cargando, setCargando] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const vacia = { contrasena_actual: '', contrasena: '', confirmar_contrasena: '' }
  const [clave, setClave] = useState(vacia)
  const [erroresClave, setErroresClave] = useState(sinErrores)
  const [avisoClave, setAvisoClave] = useState('')
  const [cambiandoClave, setCambiandoClave] = useState(false)

  async function guardar(evento) {
    evento.preventDefault()
    setCargando(true)
    setErrores(sinErrores)
    setAviso('')
    try {
      const { data } = await actualizarPerfil(datos)
      establecerUsuario(data.usuario)
      setAviso(data.mensaje)
    } catch (error) {
      setErrores(extraerErrores(error))
    } finally {
      setCargando(false)
    }
  }

  async function guardarClave(evento) {
    evento.preventDefault()
    setCambiandoClave(true)
    setErroresClave(sinErrores)
    setAvisoClave('')
    try {
      const { data } = await cambiarContrasena(clave)
      setAvisoClave(data.mensaje)
      setClave(vacia)
    } catch (error) {
      setErroresClave(extraerErrores(error))
    } finally {
      setCambiandoClave(false)
    }
  }

  function cambiarClave(evento) {
    setClave({ ...clave, [evento.target.name]: evento.target.value })
  }

  async function desactivar() {
    setErrores(sinErrores)
    try {
      const { data } = await desactivarCuenta()
      establecerUsuario(null)
      await obtenerCsrf()
      navegar('/ingreso', { state: { aviso: data.mensaje } })
    } catch (error) {
      setErrores(extraerErrores(error))
      setConfirmando(false)
    }
  }

  const campos = errores.campos

  return (
    <section className="pagina">
      <div className="contenedor">
        <h1>Mi perfil</h1>

        <div className="panel">
          <dl className="datos">
            <div><dt>Nombre de usuario</dt><dd>{usuario.nombre_usuario}</dd></div>
            <div><dt>Correo</dt><dd>{usuario.correo}</dd></div>
            <div><dt>Rol</dt><dd>{usuario.rol || 'Sin rol'}</dd></div>
            <div>
              <dt>Estado</dt>
              <dd>
                <span className={`insignia insignia-${usuario.estado.toLowerCase()}`}>
                  {ETIQUETA_ESTADO[usuario.estado]}
                </span>
              </dd>
            </div>
            <div><dt>Miembro desde</dt><dd>{fechaLegible(usuario.fecha_registro)}</dd></div>
          </dl>
        </div>

        <h2>Actualizar datos</h2>
        <form className="formulario-angosto" onSubmit={guardar} noValidate>
          <Alerta tipo="exito">{aviso}</Alerta>
          <Alerta>{errores.mensaje}</Alerta>

          <Campo etiqueta="Nombres" nombre="nombres" valor={datos.nombres} onCambio={cambiar}
            error={campos.nombres} autoComplete="given-name" />
          <Campo etiqueta="Apellidos" nombre="apellidos" valor={datos.apellidos} onCambio={cambiar}
            error={campos.apellidos} autoComplete="family-name" />
          <Campo etiqueta="Teléfono" nombre="telefono" tipo="tel" valor={datos.telefono}
            onCambio={cambiar} error={campos.telefono} autoComplete="tel" inputMode="numeric"
            ayuda="Solo números, entre 7 y 15 dígitos." />

          <Boton type="submit" cargando={cargando}>Guardar cambios</Boton>
        </form>

        <h2>Cambiar contraseña</h2>
        <form className="formulario-angosto" onSubmit={guardarClave} noValidate>
          <Alerta tipo="exito">{avisoClave}</Alerta>
          <Alerta>{erroresClave.mensaje}</Alerta>

          <Campo etiqueta="Contraseña actual" nombre="contrasena_actual" tipo="password"
            valor={clave.contrasena_actual} onCambio={cambiarClave}
            error={erroresClave.campos.contrasena_actual} autoComplete="current-password" />
          <Campo etiqueta="Contraseña nueva" nombre="contrasena" tipo="password" valor={clave.contrasena}
            onCambio={cambiarClave} error={erroresClave.campos.contrasena} autoComplete="new-password"
            ayuda="8 a 64 caracteres con mayúscula, minúscula, número y símbolo." />
          <Campo etiqueta="Confirmar contraseña nueva" nombre="confirmar_contrasena" tipo="password"
            valor={clave.confirmar_contrasena} onCambio={cambiarClave}
            error={erroresClave.campos.confirmar_contrasena} autoComplete="new-password" />

          <Boton type="submit" cargando={cambiandoClave}>Cambiar contraseña</Boton>
        </form>

        <div className="zona-peligro">
          <h2>Desactivar cuenta</h2>
          <p>Tu cuenta quedará inactiva y se cerrará tu sesión. Podrás reactivarla cuando quieras.</p>
          {confirmando ? (
            <div className="acciones" style={{ marginTop: 0 }}>
              <Boton variante="peligro" onClick={desactivar}>Sí, desactivar</Boton>
              <Boton variante="fantasma" onClick={() => setConfirmando(false)}>Cancelar</Boton>
            </div>
          ) : (
            <Boton variante="peligro" onClick={() => setConfirmando(true)}>Desactivar mi cuenta</Boton>
          )}
        </div>
      </div>
    </section>
  )
}