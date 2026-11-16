import { Link } from 'react-router-dom'
import { ETIQUETA_RESERVA, fechaLegible, pesos } from '../utils/estados'

export function FiltroEstado({ valor, onCambio }) {
  return (
    <div className="campo" style={{ minWidth: 220 }}>
      <select value={valor} onChange={(evento) => onCambio(evento.target.value)}>
        <option value="">Todos los estados</option>
        {Object.entries(ETIQUETA_RESERVA).map(([clave, texto]) => (
          <option key={clave} value={clave}>{texto}</option>
        ))}
      </select>
    </div>
  )
}

export function Historial({ reserva }) {
  return (
    <div className="historial">
      <p className="etiqueta-grupo">Historial</p>
      <ul>
        {reserva.historial.map((paso, indice) => (
          <li key={indice}>
            {new Date(paso.fecha).toLocaleString('es-CO')} · {ETIQUETA_RESERVA[paso.estado_nuevo]}
            {paso.usuario && ` · ${paso.usuario}`}{paso.detalle && ` · ${paso.detalle}`}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function FilaReserva({ reserva, mostrarHuesped = false, children }) {
  return (
    <tr>
      <td>{reserva.codigo}</td>
      <td>
        <Link to={`/alojamientos/${reserva.publicacion.id}`}>{reserva.publicacion.titulo}</Link>
        {mostrarHuesped && <span className="motivo">Huésped: {reserva.huesped}</span>}
      </td>
      <td>{fechaLegible(reserva.fecha_entrada)} → {fechaLegible(reserva.fecha_salida)}
        <span className="motivo">{reserva.noches} noches · {reserva.huespedes} huéspedes</span></td>
      <td>{pesos(reserva.total)}</td>
      <td><span className={`insignia insignia-reserva-${reserva.estado.toLowerCase()}`}>
        {ETIQUETA_RESERVA[reserva.estado]}</span></td>
      <td>{children}</td>
    </tr>
  )
}
