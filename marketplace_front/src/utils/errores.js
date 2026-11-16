export const sinErrores = {mensaje: '', campos: {}, datos: {}, estado: null}

export function extraerErrores(error) {
    const respuesta = error && error.response

    if (!respuesta) {
        return {
            ...sinErrores,
            mensaje: 'No se pudo conectar con el servidor. Revisa que el backend esté encendido.',
        }
    }

    const datos = respuesta.data
    if (!datos || typeof datos !== 'object') {
        return {
            ...sinErrores,
            estado: respuesta.status,
            mensaje: 'Ocurrió un error en el servidor. Inténtalo de nuevo.',
        }
    }

    const campos = {}
    for (const [clave, valor] of Object.entries(datos)) {
        if (Array.isArray(valor)) campos[clave] = valor.join(' ')
    }

    let mensaje = typeof datos.mensaje === 'string' ? datos.mensaje : ''
    if (campos.non_field_errors) {
        mensaje = campos.non_field_errors
        delete campos.non_field_errors
    }
    if (!mensaje) {
        mensaje = Object.keys(campos).length > 0
            ? 'Revisa los campos marcados.'
            : 'No se pudo completar la acción.'
    }

    return {mensaje, campos, datos, estado: respuesta.status}
}