import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import Campo from '../components/Campo'
import {
  actualizarPublicacion, agregarDisponibilidad, crearPublicacion, eliminarDisponibilidad, eliminarImagen,
  listarDisponibilidad, obtenerPublicacion, subirImagen, urlImagen,
} from '../api/publicaciones'
import { extraerErrores, sinErrores } from '../utils/errores'
import { ETIQUETA_PUBLICACION, TIPOS_ALOJAMIENTO, fechaLegible, hoyIso } from '../utils/estados'

const VACIA = {
  titulo: '', descripcion: '', ciudad: '', direccion: '', tipo: 'APARTAMENTO', capacidad: '2',
  precio_noche: '', tarifa_limpieza: '0', descuento_porcentaje: '0', noches_descuento: '7',
  estado: 'BORRADOR', servicios: [],
}
const ESTADOS_ANFITRION = ['BORRADOR', 'ACTIVA', 'PAUSADA']
const MAXIMO_IMAGENES = 10

function Selector({ etiqueta, nombre, valor, onCambio, opciones, error }) {
  return (
    <div className="campo">
      <label htmlFor={nombre}>{etiqueta}</label>
      <select id={nombre} name={nombre} value={valor} onChange={onCambio}>
        {Object.entries(opciones).map(([clave, texto]) => <option key={clave} value={clave}>{texto}</option>)}
      </select>
      {error && <p className="campo-error">{error}</p>}
    </div>
  )
}

export default function EditarPublicacion() {
  const { id } = useParams()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const [datos, setDatos] = useState(VACIA)
  const [errores, setErrores] = useState(sinErrores)
  const [aviso, setAviso] = useState((ubicacion.state && ubicacion.state.aviso) || '')
  const [guardando, setGuardando] = useState(false)
  const [periodos, setPeriodos] = useState([])
  const [periodo, setPeriodo] = useState({ fecha_inicio: '', fecha_fin: '' })
  const [erroresPeriodo, setErroresPeriodo] = useState(sinErrores)
  const [bloqueada, setBloqueada] = useState(false)
  const [imagenes, setImagenes] = useState([])
  const [errorImagen, setErrorImagen] = useState((ubicacion.state && ubicacion.state.errorImagen) || '')
  const [subiendo, setSubiendo] = useState(false)
  const [pendientes, setPendientes] = useState([])

  const vistas = useRef([])

  useEffect(() => () => vistas.current.forEach((vista) => URL.revokeObjectURL(vista)), [])

  useEffect(() => {
    if (!id) return
    obtenerPublicacion(id)
      .then(({ data }) => {
        setDatos({ ...data, capacidad: String(data.capacidad) })
        setBloqueada(data.estado === 'BLOQUEADA')
        setImagenes(data.imagenes)
      })
      .catch((fallo) => setErrores(extraerErrores(fallo)))
    listarDisponibilidad(id).then(({ data }) => setPeriodos(data)).catch(() => {})
  }, [id])

  function cambiar(evento) {
    setDatos({ ...datos, [evento.target.name]: evento.target.value })
  }

  function cambiarServicio(indice, campo, valor) {
    setDatos({ ...datos, servicios: datos.servicios.map((s, i) => (i === indice ? { ...s, [campo]: valor } : s)) })
  }

  async function guardar(evento) {
    evento.preventDefault()
    setGuardando(true)
    setErrores(sinErrores)
    setAviso('')
    const envio = { ...datos, servicios: datos.servicios.map(({ nombre, precio }) => ({ nombre, precio })) }
    if (!ESTADOS_ANFITRION.includes(envio.estado)) delete envio.estado
    try {
      if (id) {
        const { data } = await actualizarPublicacion(id, envio)
        setDatos({ ...data.publicacion, capacidad: String(data.publicacion.capacidad) })
        setAviso(data.mensaje)
      } else {
        const { data } = await crearPublicacion(envio)
        const nuevaId = data.publicacion.id
        let errorImagenes = ''
        for (const { archivo } of pendientes) {
          try {
            await subirImagen(nuevaId, archivo)
          } catch (fallo) {
            const { mensaje, campos: detalle } = extraerErrores(fallo)
            errorImagenes = `No se pudo subir ${archivo.name}: ${detalle.imagen || mensaje}`
            break
          }
        }
        navegar(`/publicaciones/${nuevaId}/editar`, {
          replace: true, state: { aviso: data.mensaje, errorImagen: errorImagenes },
        })
      }
    } catch (fallo) {
      setErrores(extraerErrores(fallo))
    } finally {
      setGuardando(false)
    }
  }

  async function agregarPeriodo(evento) {
    evento.preventDefault()
    setErroresPeriodo(sinErrores)
    try {
      const { data } = await agregarDisponibilidad(id, periodo)
      setPeriodos([...periodos, data.periodo].sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio)))
      setPeriodo({ fecha_inicio: '', fecha_fin: '' })
    } catch (fallo) {
      setErroresPeriodo(extraerErrores(fallo))
    }
  }

  async function quitarPeriodo(periodoId) {
    setErroresPeriodo(sinErrores)
    try {
      await eliminarDisponibilidad(id, periodoId)
      setPeriodos(periodos.filter((p) => p.id !== periodoId))
    } catch (fallo) {
      setErroresPeriodo(extraerErrores(fallo))
    }
  }

  async function agregarImagenes(evento) {
    const archivos = Array.from(evento.target.files)
    evento.target.value = ''
    setErrorImagen('')
    setSubiendo(true)
    for (const archivo of archivos) {
      try {
        const { data } = await subirImagen(id, archivo)
        setImagenes((actuales) => [...actuales, data.imagen])
      } catch (fallo) {
        const { mensaje, campos: detalle } = extraerErrores(fallo)
        setErrorImagen(`${archivo.name}: ${detalle.imagen || mensaje}`)
        break
      }
    }
    setSubiendo(false)
  }

  function elegirPendientes(evento) {
    const archivos = Array.from(evento.target.files)
    evento.target.value = ''
    const libres = MAXIMO_IMAGENES - pendientes.length
    setErrorImagen(archivos.length > libres ? `Solo puedes agregar ${MAXIMO_IMAGENES} imágenes.` : '')
    const nuevas = archivos.slice(0, libres).map((archivo) => ({ archivo, vista: URL.createObjectURL(archivo) }))
    vistas.current.push(...nuevas.map((item) => item.vista))
    setPendientes([...pendientes, ...nuevas])
  }

  async function quitarImagen(imagenId) {
    setErrorImagen('')
    try {
      await eliminarImagen(id, imagenId)
      setImagenes(imagenes.filter((imagen) => imagen.id !== imagenId))
    } catch (fallo) {
      setErrorImagen(extraerErrores(fallo).mensaje)
    }
  }

  const campos = errores.campos
  const estados = Object.fromEntries(ESTADOS_ANFITRION.map((clave) => [clave, ETIQUETA_PUBLICACION[clave]]))

  return (
    <section className="pagina">
      <div className="contenedor">
        <Link to="/mis-publicaciones">← Mis publicaciones</Link>
        <h1>{id ? 'Editar publicación' : 'Nueva publicación'}</h1>
        {bloqueada && <Alerta>Un administrador bloqueó esta publicación; no puedes modificarla.</Alerta>}

        <form className="formulario-angosto" onSubmit={guardar} noValidate>
          <Alerta tipo="exito">{aviso}</Alerta>
          <Alerta>{errores.mensaje}</Alerta>

          <Campo etiqueta="Título" nombre="titulo" valor={datos.titulo} onCambio={cambiar} error={campos.titulo} />
          <div className="campo">
            <label htmlFor="descripcion">Descripción</label>
            <textarea id="descripcion" name="descripcion" rows="4" value={datos.descripcion} onChange={cambiar} />
            {campos.descripcion && <p className="campo-error">{campos.descripcion}</p>}
          </div>
          <div className="fila-2">
            <Campo etiqueta="Ciudad" nombre="ciudad" valor={datos.ciudad} onCambio={cambiar} error={campos.ciudad} />
            <Campo etiqueta="Dirección" nombre="direccion" valor={datos.direccion} onCambio={cambiar}
              error={campos.direccion} />
          </div>
          <div className="fila-2">
            <Selector etiqueta="Tipo" nombre="tipo" valor={datos.tipo} onCambio={cambiar}
              opciones={TIPOS_ALOJAMIENTO} error={campos.tipo} />
            <Campo etiqueta="Capacidad" nombre="capacidad" tipo="number" min="1" valor={datos.capacidad}
              onCambio={cambiar} error={campos.capacidad} />
          </div>
          <div className="fila-2">
            <Campo etiqueta="Precio por noche" nombre="precio_noche" tipo="number" min="1"
              valor={datos.precio_noche} onCambio={cambiar} error={campos.precio_noche} />
            <Campo etiqueta="Tarifa de limpieza" nombre="tarifa_limpieza" tipo="number" min="0"
              valor={datos.tarifa_limpieza} onCambio={cambiar} error={campos.tarifa_limpieza} />
          </div>
          <div className="fila-2">
            <Campo etiqueta="Descuento (%)" nombre="descuento_porcentaje" tipo="number" min="0" max="90"
              valor={datos.descuento_porcentaje} onCambio={cambiar} error={campos.descuento_porcentaje} />
            <Campo etiqueta="Desde cuántas noches" nombre="noches_descuento" tipo="number" min="1"
              valor={datos.noches_descuento} onCambio={cambiar} error={campos.noches_descuento} />
          </div>
          {!bloqueada && (
            <Selector etiqueta="Estado" nombre="estado" valor={datos.estado} onCambio={cambiar}
              opciones={estados} error={campos.estado} />
          )}

          <p className="etiqueta-grupo">Servicios adicionales con costo</p>
          {datos.servicios.map((servicio, indice) => (
            <div className="fila-servicio" key={indice}>
              <input placeholder="Nombre, p. ej. Desayuno" value={servicio.nombre}
                onChange={(evento) => cambiarServicio(indice, 'nombre', evento.target.value)} />
              <input type="number" min="0" placeholder="Precio" value={servicio.precio}
                onChange={(evento) => cambiarServicio(indice, 'precio', evento.target.value)} />
              <Boton variante="fantasma" chico
                onClick={() => setDatos({ ...datos, servicios: datos.servicios.filter((_, i) => i !== indice) })}>
                Quitar
              </Boton>
            </div>
          ))}
          {campos.servicios && <p className="campo-error">{campos.servicios}</p>}
          <Boton variante="fantasma" chico
            onClick={() => setDatos({ ...datos, servicios: [...datos.servicios, { nombre: '', precio: '' }] })}>
            Agregar servicio
          </Boton>

          {!id && (
            <>
              <p className="etiqueta-grupo">Imágenes</p>
              <p className="campo-ayuda">JPG, PNG o WEBP de hasta 3 MB, máximo 10. La primera es la portada.</p>
              <Alerta>{errorImagen}</Alerta>
              {pendientes.length > 0 && (
                <div className="lista-imagenes">
                  {pendientes.map((item, indice) => (
                    <figure key={item.vista}>
                      <img src={item.vista} alt={`Imagen ${indice + 1}`} />
                      <Boton variante="fantasma" chico
                        onClick={() => {
                          URL.revokeObjectURL(item.vista)
                          setPendientes(pendientes.filter((otro) => otro !== item))
                        }}>Quitar</Boton>
                    </figure>
                  ))}
                </div>
              )}
              {pendientes.length < MAXIMO_IMAGENES && (
                <label className="boton boton-fantasma">
                  Elegir imágenes
                  <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden
                    onChange={elegirPendientes} />
                </label>
              )}
            </>
          )}

          <div className="acciones">
            <Boton type="submit" cargando={guardando} disabled={bloqueada}>
              {id ? 'Guardar cambios' : 'Crear publicación'}
            </Boton>
          </div>
        </form>

        {id && (
          <div className="zona-peligro" style={{ borderTop: 0 }}>
            <h2>Imágenes</h2>
            <p>JPG, PNG o WEBP de hasta 3 MB, máximo 10. La primera es la portada.</p>
            <Alerta>{errorImagen}</Alerta>
            {imagenes.length === 0 ? <p className="vacio">Aún no hay imágenes.</p> : (
              <div className="lista-imagenes">
                {imagenes.map((imagen, indice) => (
                  <figure key={imagen.id}>
                    <img src={urlImagen(id, imagen.id)} alt={`Imagen ${indice + 1}`} />
                    {!bloqueada && (
                      <Boton variante="fantasma" chico onClick={() => quitarImagen(imagen.id)}>Eliminar</Boton>
                    )}
                  </figure>
                ))}
              </div>
            )}
            {!bloqueada && imagenes.length < 10 && (
              <label className="boton boton-fantasma">
                {subiendo ? 'Subiendo...' : 'Agregar imágenes'}
                <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden
                  disabled={subiendo} onChange={agregarImagenes} />
              </label>
            )}
          </div>
        )}

        {id && (
          <div className="zona-peligro" style={{ borderTop: 0 }}>
            <h2>Disponibilidad</h2>
            <p>Registra los periodos en que recibes huéspedes. La fecha de fin es la última salida posible.</p>
            <Alerta>{erroresPeriodo.mensaje}</Alerta>
            {periodos.length === 0 ? <p className="vacio">Sin periodos registrados: nadie podrá reservar.</p> : (
              <ul className="lista-periodos">
                {periodos.map((p) => (
                  <li key={p.id}>
                    Del {fechaLegible(p.fecha_inicio)} al {fechaLegible(p.fecha_fin)}
                    <Boton variante="fantasma" chico onClick={() => quitarPeriodo(p.id)}>Eliminar</Boton>
                  </li>
                ))}
              </ul>
            )}
            <form onSubmit={agregarPeriodo} noValidate>
              <div className="fila-2">
                <Campo etiqueta="Desde" nombre="fecha_inicio" tipo="date" min={hoyIso()} valor={periodo.fecha_inicio}
                  onCambio={(e) => setPeriodo({ ...periodo, fecha_inicio: e.target.value })}
                  error={erroresPeriodo.campos.fecha_inicio} />
                <Campo etiqueta="Hasta" nombre="fecha_fin" tipo="date" min={periodo.fecha_inicio || hoyIso(1)}
                  valor={periodo.fecha_fin} onCambio={(e) => setPeriodo({ ...periodo, fecha_fin: e.target.value })}
                  error={erroresPeriodo.campos.fecha_fin} />
              </div>
              <Boton type="submit" variante="fantasma">Agregar periodo</Boton>
            </form>
          </div>
        )}
      </div>
    </section>
  )
}
