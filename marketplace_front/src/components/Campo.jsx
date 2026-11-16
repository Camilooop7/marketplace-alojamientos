import { useState } from 'react'

export default function Campo({ etiqueta, nombre, tipo = 'text', valor, onCambio, error, ayuda, ...resto }) {
  const [visible, setVisible] = useState(false)
  const esClave = tipo === 'password'
  const clases = [error ? 'invalido' : '', esClave ? 'con-boton' : ''].join(' ').trim()

  return (
    <div className="campo">
      <label htmlFor={nombre}>{etiqueta}</label>
      <div className="entrada">
        <input
          id={nombre}
          name={nombre}
          type={esClave && visible ? 'text' : tipo}
          value={valor}
          onChange={onCambio}
          className={clases}
          aria-invalid={Boolean(error)}
          {...resto}
        />
        {esClave && (
          <button type="button" className="ver-clave" onClick={() => setVisible(!visible)}>
            {visible ? 'Ocultar' : 'Mostrar'}
          </button>
        )}
      </div>
      {error ? <p className="campo-error">{error}</p> : ayuda ? <p className="campo-ayuda">{ayuda}</p> : null}
    </div>
  )
}