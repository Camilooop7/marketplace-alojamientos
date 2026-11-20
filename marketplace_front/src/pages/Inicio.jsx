import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Alerta from '../components/Alerta'
import TarjetaAlojamiento from '../components/TarjetaAlojamiento'
import { listarPublicaciones } from '../api/publicaciones'

export default function Inicio() {
  const ubicacion = useLocation()
  const aviso = ubicacion.state && ubicacion.state.aviso
  const [lista, setLista] = useState([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    listarPublicaciones({})
      .then(({ data }) => setLista(data))
      .catch(() => setLista([]))
      .finally(() => setCargando(false))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="contenedor">
          <Alerta>{aviso}</Alerta>
          <h1>Un lugar donde quedarse.</h1>
          <p>
            Marketplace de alojamientos. Busca dónde quedarte o revisa lo que ya tienes en marcha.
          </p>
          <div className="acciones">
            <Link className="boton boton-fantasma" to="/alojamientos">Ver alojamientos</Link>
            <Link className="boton boton-primario" to="/perfil">Ir a mi perfil</Link>
          </div>
        </div>
      </section>

      <section className="seccion">
        <div className="contenedor">
          <p className="etiqueta-seccion">Alojamientos</p>
          <h2>Elige dónde quedarte.</h2>
          {cargando ? (
            <p className="cargando">Cargando alojamientos...</p>
          ) : lista.length === 0 ? (
            <p className="vacio">Todavía no hay alojamientos publicados.</p>
          ) : (
            <div className="rejilla">
              {lista.map((item) => <TarjetaAlojamiento key={item.id} item={item} />)}
            </div>
          )}
        </div>
      </section>

    </>
  )
}