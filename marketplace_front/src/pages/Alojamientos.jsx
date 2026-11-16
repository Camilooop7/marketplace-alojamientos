import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import { listarPublicaciones, urlImagen } from '../api/publicaciones'
import { extraerErrores } from '../utils/errores'
import { TIPOS_ALOJAMIENTO, pesos } from '../utils/estados'

const ICONOS = {
  billete: 'M3,6H21V18H3V6M12,9A3,3 0 0,1 15,12A3,3 0 0,1 12,15A3,3 0 0,1 9,12A3,3 0 0,1 12,9M7,8A2,2 0 0,1 5,10V14A2,2 0 0,1 7,16H17A2,2 0 0,1 19,14V10A2,2 0 0,1 17,8H7Z',
  lugar: 'M12,11.5A2.5,2.5 0 0,1 9.5,9A2.5,2.5 0 0,1 12,6.5A2.5,2.5 0 0,1 14.5,9A2.5,2.5 0 0,1 12,11.5M12,2A7,7 0 0,0 5,9C5,14.25 12,22 12,22C12,22 19,14.25 19,9A7,7 0 0,0 12,2Z',
  personas: 'M16,13C15.71,13 15.38,13 15.03,13.05C16.19,13.89 17,15 17,16.5V19H23V16.5C23,14.17 18.33,13 16,13M8,13C5.67,13 1,14.17 1,16.5V19H15V16.5C15,14.17 10.33,13 8,13M8,11A3,3 0 0,0 11,8A3,3 0 0,0 8,5A3,3 0 0,0 5,8A3,3 0 0,0 8,11M16,11A3,3 0 0,0 19,8A3,3 0 0,0 16,5A3,3 0 0,0 13,8A3,3 0 0,0 16,11Z',
}

function Icono({ trazo }) {
  return (
    <svg className="icono" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="currentColor" d={trazo} />
    </svg>
  )
}

export default function Alojamientos() {
  const [filtros, setFiltros] = useState({ ciudad: '', huespedes: '' })
  const [lista, setLista] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  async function buscar(evento) {
    if (evento) evento.preventDefault()
    setCargando(true)
    setError('')
    try {
      const { data } = await listarPublicaciones(filtros)
      setLista(data)
    } catch (fallo) {
      setError(extraerErrores(fallo).mensaje)
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    listarPublicaciones({})
      .then(({ data }) => setLista(data))
      .catch((fallo) => setError(extraerErrores(fallo).mensaje))
      .finally(() => setCargando(false))
  }, [])

  function cambiar(evento) {
    setFiltros({ ...filtros, [evento.target.name]: evento.target.value })
  }

  return (
    <section className="pagina">
      <div className="contenedor">
        <div className="cabecera">
          <h1>Alojamientos</h1>
          <p>Casas, apartamentos, cabañas y habitaciones en toda Colombia.</p>
          <form className="barra-herramientas" onSubmit={buscar}>
            <div className="entrada">
              <input name="ciudad" placeholder="Ciudad" value={filtros.ciudad} onChange={cambiar} />
            </div>
            <div className="entrada" style={{ maxWidth: 180 }}>
              <input name="huespedes" type="number" min="1" placeholder="Huéspedes"
                value={filtros.huespedes} onChange={cambiar} />
            </div>
            <Boton type="submit">Buscar</Boton>
          </form>
        </div>

        <Alerta>{error}</Alerta>

        {cargando ? (
          <p className="cargando">Buscando alojamientos...</p>
        ) : lista.length === 0 ? (
          <p className="vacio">No encontramos alojamientos con esos filtros. Prueba con otra ciudad o menos huéspedes.</p>
        ) : (
          <div className="rejilla">
            {lista.map((item) => (
              <Link key={item.id} to={`/alojamientos/${item.id}`} className="ficha"
                style={item.imagenes.length > 0
                  ? { backgroundImage: `url(${urlImagen(item.id, item.imagenes[0].id)})` } : undefined}>
                {item.imagenes.length === 0 && <span className="ficha-sin-imagen">Sin imágenes</span>}
                <div className="ficha-portada">
                  <span className="ficha-tipo">{TIPOS_ALOJAMIENTO[item.tipo]}</span>
                  <span className="ficha-boton">Ver alojamiento</span>
                </div>
                <div className="ficha-info">
                  <h3 className="ficha-titulo">{item.titulo}</h3>
                  <p className="ficha-precio">
                    <Icono trazo={ICONOS.billete} />
                    <span><strong>{pesos(item.precio_noche)}</strong> por noche</span>
                  </p>
                  <div className="ficha-mas">
                    <div>
                      <div className="ficha-datos">
                        <span className="ficha-dato ficha-dato-lugar">
                          <Icono trazo={ICONOS.lugar} />{item.ciudad}
                        </span>
                        <span className="ficha-dato">
                          <Icono trazo={ICONOS.personas} />Hasta {item.capacidad} huéspedes
                        </span>
                      </div>
                      <p className="ficha-texto">{item.descripcion}</p>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
