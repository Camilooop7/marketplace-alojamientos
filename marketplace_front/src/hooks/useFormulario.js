import {useState} from 'react'

export default function useFormulario(inicial) {
    const [datos, setDatos] = useState(inicial)

    function cambiar(evento) {
        const {name, value} = evento.target
        setDatos((previo) => ({...previo, [name]: value}))
    }

    return [datos, cambiar, setDatos]
}