import { useEffect, useState } from 'react'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import TarjetaAlojamiento from '../components/TarjetaAlojamiento'
import { listarPublicaciones } from '../api/publicaciones'
import { extraerErrores } from '../utils/errores'

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
            {lista.map((item) => <TarjetaAlojamiento key={item.id} item={item} />)}
          </div>
        )}
      </div>
    </section>
  )
}
