import {Outlet} from 'react-router-dom'
import BarraNavegacion from './BarraNavegacion'

export default function Estructura() {
    return (
        <div className="estructura">
            <BarraNavegacion/>
            <main className="contenido">
                <Outlet/>
            </main>
            <footer className="pie">
                <div className="contenedor">Marketplace de alojamientos · Ingeniería de Software 1</div>
            </footer>
        </div>
    )
}