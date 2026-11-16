import {useEffect, useState} from 'react'
import {ContextoAuth} from './contextoAuth'
import {
    obtenerCsrf,
    obtenerPerfil,
    ingresar as ingresarApi,
    salir as salirApi,
} from '../api/usuarios'

export default function ProveedorAuth({children}) {
    const [usuario, setUsuario] = useState(null)
    const [cargando, setCargando] = useState(true)

    useEffect(() => {
        async function iniciar() {
            try {
                await obtenerCsrf()
                const {data} = await obtenerPerfil()
                if (data.estado === 'ACTIVO') setUsuario(data)
            } catch {
                setUsuario(null)
            } finally {
                setCargando(false)
            }
        }

        iniciar()
    }, [])

    async function ingresar(correoOUsuario, contrasena) {
        const {data} = await ingresarApi(correoOUsuario, contrasena)
        setUsuario(data.usuario)
        return data
    }

    async function salir() {
        try {
            await salirApi()
        } finally {
            setUsuario(null)
            obtenerCsrf().catch(() => {
            })
        }
    }

    const esAdministrador = Boolean(
        usuario && usuario.rol && usuario.rol.split(', ').includes('Administrador'),
    )

    const valor = {usuario, cargando, esAdministrador, ingresar, salir, establecerUsuario: setUsuario}

    return <ContextoAuth.Provider value={valor}>{children}</ContextoAuth.Provider>
}