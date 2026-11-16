import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alerta from '../components/Alerta'
import { misPublicaciones } from '../api/publicaciones'
import { extraerErrores } from '../utils/errores'
import { ETIQUETA_PUBLICACION, TIPOS_ALOJAMIENTO, pesos } from '../utils/estados'

export default function MisPublicaciones() {
  const [lista, setLista] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    misPublicaciones()
      .then(({ data }) => setLista(data))
      .catch((fallo) => setError(extraerErrores(fallo).mensaje))
      .finally(() => setCargando(false))
  }, [])

  return (
    <section className="pagina">
      <div className="contenedor">
        <h1>Mis publicaciones</h1>
        <Alerta>{error}</Alerta>
        <div className="barra-herramientas">
          <Link className="boton boton-primario" to="/publicaciones/nueva">Nueva publicación</Link>
        </div>

        {cargando ? <p className="cargando">Cargando publicaciones...</p> : lista.length === 0 ? (
          <p className="vacio">Aún no tienes publicaciones. Crea la primera para empezar a recibir reservas.</p>
        ) : (
          <div className="tabla-contenedor">
            <table>
              <thead>
                <tr><th>Título</th><th>Tipo</th><th>Ciudad</th><th>Precio por noche</th><th>Estado</th><th>Acciones</th></tr>
              </thead>
              <tbody>
                {lista.map((item) => (
                  <tr key={item.id}>
                    <td>{item.titulo}</td>
                    <td>{TIPOS_ALOJAMIENTO[item.tipo]}</td>
                    <td>{item.ciudad}</td>
                    <td>{pesos(item.precio_noche)}</td>
                    <td><span className={`insignia insignia-publicacion-${item.estado.toLowerCase()}`}>
                      {ETIQUETA_PUBLICACION[item.estado]}</span></td>
                    <td className="botones">
                      <Link className="boton boton-fantasma boton-chico" to={`/publicaciones/${item.id}/editar`}>Editar</Link>
                      {item.estado === 'ACTIVA' && (
                        <Link className="boton boton-fantasma boton-chico" to={`/alojamientos/${item.id}`}>Ver</Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
