import {Link} from 'react-router-dom'

export default function DisenoAuth({titulo, subtitulo, children, pie}) {
    return (
        <main className="auth">
            <aside className="auth-panel">
                <Link to="/" className="marca">Marketplace</Link>
                <div>
                    <h2 className="auth-gigante">
                        Market<br/><span className="resalte">place</span>
                    </h2>
                    <p className="auth-lema">Encuentra o publica el lugar ideal para quedarte.</p>
                </div>
            </aside>
            <section className="auth-contenido">
                <div className="auth-caja">
                    <h1 className="titulo-formulario">{titulo}</h1>
                    {subtitulo && <p className="subtitulo">{subtitulo}</p>}
                    {children}
                    {pie && <p className="auth-pie">{pie}</p>}
                </div>
            </section>
        </main>
    )
}