import { useState } from 'react'
import { urlImagen } from '../api/publicaciones'

export default function Galeria({ publicacion }) {
  const [actual, setActual] = useState(0)
  const imagenes = publicacion.imagenes || []
  if (imagenes.length === 0) return <div className="galeria-vacia">Sin imágenes</div>
  const indice = Math.min(actual, imagenes.length - 1)

  return (
    <div className="galeria">
      <img className="galeria-principal" src={urlImagen(publicacion.id, imagenes[indice].id)}
        alt={`${publicacion.titulo}, imagen ${indice + 1} de ${imagenes.length}`} />
      {imagenes.length > 1 && (
        <div className="galeria-miniaturas">
          {imagenes.map((imagen, i) => (
            <button key={imagen.id} type="button" className={i === indice ? 'activa' : ''}
              onClick={() => setActual(i)} aria-label={`Ver imagen ${i + 1}`}>
              <img src={urlImagen(publicacion.id, imagen.id)} alt="" loading="lazy" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
