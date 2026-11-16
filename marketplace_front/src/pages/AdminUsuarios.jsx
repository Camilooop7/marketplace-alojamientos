import {useEffect, useState} from 'react'
import Alerta from '../components/Alerta'
import Boton from '../components/Boton'
import {useAuth} from '../context/contextoAuth'
import {liberarUsuario, listarUsuarios, restringirUsuario} from '../api/usuarios'
import {extraerErrores, sinErrores} from '../utils/errores'
import {ETIQUETA_ESTADO} from '../utils/estados'

export default function AdminUsuarios() {
    const {usuario} = useAuth()
    const [usuarios, setUsuarios] = useState([])
    const [cargando, setCargando] = useState(true)
    const [errores, setErrores] = useState(sinErrores)
    const [aviso, setAviso] = useState('')
    const [busqueda, setBusqueda] = useState('')
    const [restringiendo, setRestringiendo] = useState(null)
    const [motivo, setMotivo] = useState('')

    useEffect(() => {
        listarUsuarios()
            .then(({data}) => setUsuarios(data))
            .catch((error) => setErrores(extraerErrores(error)))
            .finally(() => setCargando(false))
    }, [])

    function reemplazar(nuevo) {
        setUsuarios((lista) => lista.map((item) => (item.id === nuevo.id ? nuevo : item)))
    }

    function abrirRestriccion(id) {
        setRestringiendo(id)
        setMotivo('')
        setErrores(sinErrores)
    }

    async function confirmarRestriccion(evento, id) {
        evento.preventDefault()
        setErrores(sinErrores)
        setAviso('')
        try {
            const {data} = await restringirUsuario(id, motivo)
            reemplazar(data.usuario)
            setAviso(data.mensaje)
            setRestringiendo(null)
        } catch (error) {
            setErrores(extraerErrores(error))
        }
    }

    async function liberar(id) {
        setErrores(sinErrores)
        setAviso('')
        try {
            const {data} = await liberarUsuario(id)
            reemplazar(data.usuario)
            setAviso(data.mensaje)
        } catch (error) {
            setErrores(extraerErrores(error))
        }
    }

    const texto = busqueda.trim().toLowerCase()
    const visibles = usuarios.filter((item) =>
        `${item.nombres} ${item.apellidos} ${item.nombre_usuario} ${item.correo}`
            .toLowerCase()
            .includes(texto),
    )

    return (
        <section className="pagina">
            <div className="contenedor">
                <h1>Usuarios</h1>

                <Alerta tipo="exito">{aviso}</Alerta>
                <Alerta>{errores.mensaje}</Alerta>

                <div className="barra-herramientas">
                    <div className="entrada">
                        <input
                            type="search"
                            placeholder="Buscar por nombre, usuario o correo"
                            value={busqueda}
                            onChange={(evento) => setBusqueda(evento.target.value)}
                        />
                    </div>
                </div>

                {cargando ? (
                    <p className="cargando">Cargando usuarios...</p>
                ) : (
                    <div className="tabla-contenedor">
                        <table>
                            <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Usuario</th>
                                <th>Correo</th>
                                <th>Rol</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                            </thead>
                            <tbody>
                            {visibles.length === 0 && (
                                <tr>
                                    <td colSpan={6}>No hay usuarios para mostrar.</td>
                                </tr>
                            )}
                            {visibles.map((item) => (
                                <tr key={item.id}>
                                    <td>{item.nombres} {item.apellidos}</td>
                                    <td>{item.nombre_usuario}</td>
                                    <td>{item.correo}</td>
                                    <td>{item.rol || '—'}</td>
                                    <td>
                      <span className={`insignia insignia-${item.estado.toLowerCase()}`}>
                        {ETIQUETA_ESTADO[item.estado]}
                      </span>
                                        {item.estado === 'RESTRINGIDO' && item.motivo_restriccion && (
                                            <span className="motivo">{item.motivo_restriccion}</span>
                                        )}
                                    </td>
                                    <td>
                                        {item.id === usuario.id ? (
                                            'Tú'
                                        ) : item.estado === 'RESTRINGIDO' ? (
                                            <Boton variante="fantasma" chico onClick={() => liberar(item.id)}>
                                                Liberar
                                            </Boton>
                                        ) : restringiendo === item.id ? (
                                            <form className="form-linea"
                                                  onSubmit={(evento) => confirmarRestriccion(evento, item.id)}>
                                                <input
                                                    placeholder="Motivo de la restricción"
                                                    value={motivo}
                                                    onChange={(evento) => setMotivo(evento.target.value)}
                                                    autoFocus
                                                />
                                                {errores.campos.motivo &&
                                                    <span className="campo-error">{errores.campos.motivo}</span>}
                                                <div className="botones">
                                                    <Boton type="submit" variante="peligro" chico>Confirmar</Boton>
                                                    <Boton variante="fantasma" chico
                                                           onClick={() => setRestringiendo(null)}>
                                                        Cancelar
                                                    </Boton>
                                                </div>
                                            </form>
                                        ) : (
                                            <Boton variante="peligro" chico onClick={() => abrirRestriccion(item.id)}>
                                                Restringir
                                            </Boton>
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