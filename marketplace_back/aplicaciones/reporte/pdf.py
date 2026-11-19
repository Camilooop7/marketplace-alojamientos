import math
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import CondPageBreak, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from aplicaciones.reserva.factura import (
    ANCHO, AZUL, BORDE, BORDE_SUAVE, BRUMA, CENIZA, COBALTO, CUARZO, ETIQUETA, ETIQUETA_DERECHA, LILA, LOGO,
    EMPRESA, PROFUNDO, TINTA, estilo, fecha, fecha_corta, franja, pesos,
)
from aplicaciones.reserva.models import Reserva

VERDE = '#1f8a5b'
COLOR_ESTADO = {
    Reserva.Estado.PENDIENTE_PAGO: '#9a6100',
    Reserva.Estado.CONFIRMADA: VERDE,
    Reserva.Estado.COMPLETADA: VERDE,
    Reserva.Estado.CANCELADA: '#b3261e',
}
ESTADO_CORTO = {
    Reserva.Estado.PENDIENTE_PAGO: 'Pendiente',
    Reserva.Estado.CONFIRMADA: 'Confirmada',
    Reserva.Estado.COMPLETADA: 'Completada',
    Reserva.Estado.CANCELADA: 'Cancelada',
}
SEPARACION = 8

NOMBRE = estilo('nombre', fontName='Helvetica-Bold', fontSize=20, leading=24, alignment=TA_RIGHT)
DATO_DERECHA = estilo('dato_derecha', fontSize=9, leading=13, textColor=CENIZA, alignment=TA_RIGHT)
SECCION = estilo('seccion', fontName='Helvetica-Bold', fontSize=13, leading=18)
SECCION_NOTA = estilo('seccion_nota', fontSize=8.5, leading=12, textColor=CENIZA)
TARJETA_ETIQUETA = estilo('tarjeta_etiqueta', fontName='Helvetica-Bold', fontSize=6.5, leading=9, textColor=CENIZA)
TARJETA_VALOR = estilo('tarjeta_valor', fontName='Helvetica-Bold', fontSize=14, leading=18)
DESTACADA_ETIQUETA = estilo('destacada_etiqueta', fontName='Helvetica-Bold', fontSize=6.5, leading=9, textColor=LILA)
DESTACADA_VALOR = estilo('destacada_valor', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=CUARZO)
CABEZA = estilo('cabeza', fontName='Helvetica-Bold', fontSize=6.5, leading=9, textColor=CENIZA)
CABEZA_DERECHA = estilo('cabeza_derecha', fontName='Helvetica-Bold', fontSize=6.5, leading=9, textColor=CENIZA,
                        alignment=TA_RIGHT)
CELDA = estilo('celda_reporte', fontSize=8, leading=10.5, textColor=TINTA)
CELDA_DERECHA = estilo('celda_reporte_derecha', fontSize=8, leading=10.5, textColor=TINTA, alignment=TA_RIGHT)
CELDA_NOTA = estilo('celda_nota', fontSize=7, leading=9, textColor=CENIZA)
TOTAL_CELDA = estilo('total_celda', fontName='Helvetica-Bold', fontSize=8, leading=10.5)
TOTAL_DERECHA = estilo('total_derecha', fontName='Helvetica-Bold', fontSize=8, leading=10.5, alignment=TA_RIGHT)
VACIO = estilo('vacio', fontSize=9, leading=13, textColor=CENIZA)
ESTADOS = estilo('estados', fontSize=8, leading=11, textColor=BRUMA)


def entero(valor):
    return '{0:,}'.format(int(valor)).replace(',', '.')


def decimal(valor):
    return '{0:.1f}'.format(float(valor)).replace('.', ',')


def escala(maximo):
    if maximo <= 0:
        return 1
    bruto = maximo * 1.08 / 3
    potencia = 10 ** math.floor(math.log10(bruto))
    for factor in (1, 2, 2.5, 5, 10):
        if factor * potencia >= bruto:
            return factor * potencia * 3


def abreviado(valor):
    valor = float(valor)
    if valor >= 1000000:
        return '$ {0} M'.format(decimal(valor / 1000000))
    if valor >= 1000:
        return '$ {0} mil'.format(entero(round(valor / 1000)))
    return pesos(valor)


def texto(valor, estilo_parrafo=CELDA):
    return Paragraph(escape(str(valor)), estilo_parrafo)


def doble(principal, secundario):
    return [texto(principal), texto(secundario, CELDA_NOTA)]


def describir_periodo(periodo):
    desde, hasta = periodo['desde'], periodo['hasta']
    if desde and hasta:
        return 'Del {0} al {1}'.format(fecha_corta(desde), fecha_corta(hasta))
    if desde:
        return 'Desde el {0}'.format(fecha_corta(desde))
    if hasta:
        return 'Hasta el {0}'.format(fecha_corta(hasta))
    return 'Todo el historial'


def encabezado(etiqueta, titulo, subtitulo, reporte):
    derecha = [Paragraph(etiqueta, ETIQUETA_DERECHA), Spacer(1, 4), Paragraph(escape(titulo), NOMBRE)]
    if subtitulo:
        derecha.append(Paragraph(escape(subtitulo), DATO_DERECHA))
    derecha += [Spacer(1, 6), Paragraph(describir_periodo(reporte['periodo']), DATO_DERECHA),
                Paragraph('Generado el {0}'.format(fecha(timezone.localtime(reporte['generado']))), DATO_DERECHA)]
    tabla = Table([[
        [Paragraph('MARKET<br/><font color="#305fbd">PLACE</font>', LOGO), Spacer(1, 8),
         Paragraph('Inversiones LR', EMPRESA)],
        derecha,
    ]], colWidths=[ANCHO * 0.4, ANCHO * 0.6])
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20), ('LINEBELOW', (0, 0), (-1, 0), 0.6, BORDE),
    ]))
    return tabla


def tarjeta(etiqueta, valor, ancho, destacada=False):
    estilos = (DESTACADA_ETIQUETA, DESTACADA_VALOR) if destacada else (TARJETA_ETIQUETA, TARJETA_VALOR)
    tabla = Table([[[Paragraph(etiqueta.upper(), estilos[0]), Spacer(1, 6), Paragraph(escape(valor), estilos[1])]]],
                  colWidths=[ancho])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COBALTO if destacada else PROFUNDO),
        ('BOX', (0, 0), (-1, -1), 0.8, COBALTO if destacada else BORDE), ('ROUNDEDCORNERS', [8] * 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 11), ('RIGHTPADDING', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    return tabla


def indicadores(filas):
    ancho = (ANCHO - 3 * SEPARACION) / 4
    celdas = [[tarjeta(*datos, ancho=ancho, destacada=indice == 0 and fila == 0)
               for indice, datos in enumerate(grupo)] for fila, grupo in enumerate(filas)]
    tabla = Table(celdas, colWidths=[ancho + SEPARACION] * 3 + [ancho])
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), SEPARACION),
    ]))
    return tabla


def tarjetas_ingresos(resumen):
    return [
        ('Ingresos facturados', pesos(resumen['ingresos'])),
        ('Confirmados', pesos(resumen['ingresos_confirmados'])),
        ('Por cobrar', pesos(resumen['ingresos_pendientes'])),
        ('Reservas', entero(resumen['reservas'])),
    ]


def linea_estados(estados):
    partes = ['<font color="{0}">&#9679;</font>  {1} <b>{2}</b>'.format(
        COLOR_ESTADO[dato['estado']], escape(dato['etiqueta']), entero(dato['cantidad'])) for dato in estados]
    return Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.join(partes), ESTADOS)


def titulo_seccion(titulo, nota=''):
    partes = [CondPageBreak(6 * cm), Spacer(1, 22), Paragraph(titulo, SECCION)]
    if nota:
        partes.append(Paragraph(nota, SECCION_NOTA))
    partes.append(Spacer(1, 10))
    return partes


def grafico_meses(meses):
    alto, izquierda, abajo, arriba = 150, 46, 22, 18
    dibujo = Drawing(ANCHO - 28, alto)
    ancho_util = ANCHO - 28 - izquierda
    maximo = max(float(mes['ingresos']) for mes in meses)
    tope = escala(maximo)
    altura_util = alto - abajo - arriba
    for paso in range(4):
        y = abajo + altura_util * paso / 3
        dibujo.add(Line(izquierda, y, ANCHO - 28, y, strokeColor=BORDE if paso else BRUMA,
                        strokeWidth=0.5 if paso else 0.8))
        dibujo.add(String(izquierda - 6, y - 2.5, abreviado(tope * paso / 3), fontName='Helvetica',
                          fontSize=6.5, fillColor=CENIZA, textAnchor='end'))
    espacio = ancho_util / len(meses)
    barra = min(34, espacio * 0.62)
    salto = math.ceil(len(meses) / 12)
    for indice, mes in enumerate(meses):
        valor = float(mes['ingresos'])
        centro = izquierda + espacio * (indice + 0.5)
        altura = altura_util * valor / tope
        if altura > 0:
            radio = min(4, altura / 2, barra / 2)
            dibujo.add(Rect(centro - barra / 2, abajo, barra, altura, rx=radio, ry=radio,
                            fillColor=AZUL, strokeColor=None))
            dibujo.add(Rect(centro - barra / 2, abajo, barra, min(radio, altura), fillColor=AZUL, strokeColor=None))
        if valor == maximo and maximo > 0:
            dibujo.add(String(centro, abajo + altura + 5, pesos(valor), fontName='Helvetica-Bold', fontSize=7,
                              fillColor=TINTA, textAnchor='middle'))
        if indice % salto == 0:
            dibujo.add(String(centro, abajo - 12, mes['etiqueta'], fontName='Helvetica', fontSize=6.5,
                              fillColor=CENIZA, textAnchor='middle'))
    caja = Table([[dibujo]], colWidths=[ANCHO])
    caja.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.8, BORDE), ('ROUNDEDCORNERS', [10] * 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 14), ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 14), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return caja


def tabla(encabezados, filas, proporciones, total=None, relleno=8):
    derecha = [indice for indice, (_, alineacion) in enumerate(encabezados) if alineacion == 'derecha']
    cabeza = [Paragraph(nombre.upper(), CABEZA_DERECHA if indice in derecha else CABEZA)
              for indice, (nombre, _) in enumerate(encabezados)]
    cuerpo = []
    for fila in filas:
        cuerpo.append([celda if not isinstance(celda, (str, int)) else
                       texto(celda, CELDA_DERECHA if indice in derecha else CELDA)
                       for indice, celda in enumerate(fila)])
    if total:
        cuerpo.append([texto(celda, TOTAL_DERECHA if indice in derecha else TOTAL_CELDA)
                       for indice, celda in enumerate(total)])
    resultado = Table([cabeza] + cuerpo, colWidths=[ANCHO * parte for parte in proporciones], repeatRows=1)
    estilos = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), PROFUNDO), ('BOX', (0, 0), (-1, -1), 0.8, BORDE),
        ('ROUNDEDCORNERS', [8] * 4), ('LINEBELOW', (0, 0), (-1, 0), 0.6, BORDE),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, BORDE_SUAVE),
        ('LEFTPADDING', (0, 0), (-1, -1), relleno), ('RIGHTPADDING', (0, 0), (-1, -1), relleno),
        ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]
    if total:
        estilos += [('BACKGROUND', (0, -1), (-1, -1), PROFUNDO), ('LINEABOVE', (0, -1), (-1, -1), 0.6, BORDE)]
    resultado.setStyle(TableStyle(estilos))
    return resultado


def vacio(mensaje):
    return Paragraph(mensaje, VACIO)


def seccion_meses(reporte):
    partes = titulo_seccion('Ingresos por mes', 'Valor facturado según el mes de entrada de cada reserva.')
    if not reporte['meses']:
        return partes + [vacio('No hay reservas en este periodo.')]
    return [KeepTogether(partes + [grafico_meses(reporte['meses'])])]


def celda_estado(estado):
    return Paragraph('<font color="{0}">&#9679;</font> {1}'.format(COLOR_ESTADO[estado], ESTADO_CORTO[estado]), CELDA)


def documento(contenido, titulo):
    def pie(lienzo, plantilla):
        franja(lienzo, plantilla)
        izquierda = plantilla.leftMargin + 6
        lienzo.saveState()
        lienzo.setStrokeColor(BORDE)
        lienzo.setLineWidth(0.6)
        lienzo.line(izquierda, 1.6 * cm, izquierda + ANCHO, 1.6 * cm)
        lienzo.setStrokeColor(AZUL)
        lienzo.setLineWidth(2)
        lienzo.line(izquierda, 1.6 * cm, izquierda + 40, 1.6 * cm)
        lienzo.setFont('Helvetica', 8)
        lienzo.setFillColor(CENIZA)
        lienzo.drawString(izquierda, 1.15 * cm, 'Marketplace de Alojamientos · Inversiones LR')
        lienzo.drawRightString(izquierda + ANCHO, 1.15 * cm, '{0} · Página {1}'.format(titulo, lienzo.getPageNumber()))
        lienzo.restoreState()

    salida = BytesIO()
    SimpleDocTemplate(salida, pagesize=letter, title=titulo, author='Marketplace de Alojamientos',
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                      bottomMargin=2.2 * cm).build(contenido, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()


def pdf_anfitrion(reporte):
    resumen = reporte['resumen']
    anfitrion = reporte['anfitrion']
    contenido = [
        encabezado('REPORTE DE ANFITRIÓN', anfitrion['nombre'],
                   '{0} · {1}'.format(anfitrion['usuario'], anfitrion['correo']), reporte),
        Spacer(1, 22),
        indicadores([tarjetas_ingresos(resumen), [
            ('Noches reservadas', entero(resumen['noches'])),
            ('Huéspedes alojados', entero(resumen['huespedes'])),
            ('Alojamientos', entero(resumen['alojamientos'])),
            ('Canceladas', entero(resumen['canceladas'])),
        ]]),
        Spacer(1, 4),
        linea_estados(reporte['estados']),
        *seccion_meses(reporte),
        *titulo_seccion('Rendimiento por alojamiento'),
    ]
    if reporte['alojamientos']:
        filas = [[doble(fila['titulo'], '{0} · {1}'.format(fila['tipo_etiqueta'], fila['ciudad'])),
                  entero(fila['reservas']), entero(fila['noches']), entero(fila['huespedes']),
                  pesos(fila['ingresos'])]
                 for fila in reporte['alojamientos']]
        contenido.append(tabla([('Alojamiento', ''), ('Reservas', 'derecha'), ('Noches', 'derecha'),
                                ('Huéspedes', 'derecha'), ('Ingresos', 'derecha')],
                               filas, [0.44, 0.13, 0.12, 0.13, 0.18]))
    else:
        contenido.append(vacio('Este anfitrión todavía no tiene alojamientos.'))
    contenido += titulo_seccion('Quiénes reservan', 'Huéspedes con reservas vigentes, ordenados por valor facturado.')
    if reporte['clientes']:
        filas = [[doble(fila['nombre'], fila['correo']), entero(fila['reservas']), entero(fila['noches']),
                  entero(fila['huespedes']), pesos(fila['ingresos'])] for fila in reporte['clientes']]
        contenido.append(tabla([('Huésped', ''), ('Reservas', 'derecha'), ('Noches', 'derecha'),
                                ('Personas', 'derecha'), ('Total', 'derecha')],
                               filas, [0.43, 0.12, 0.12, 0.13, 0.2]))
    else:
        contenido.append(vacio('No hay huéspedes con reservas vigentes en este periodo.'))
    contenido += titulo_seccion('Detalle de reservas', 'El total no incluye las reservas canceladas.')
    if reporte['reservas']:
        filas = [[texto(fila['codigo']), texto(fila['huesped']), texto(fila['alojamiento']),
                  texto(fecha_corta(fila['fecha_entrada'])), entero(fila['noches']), entero(fila['huespedes']),
                  pesos(fila['total']), celda_estado(fila['estado'])] for fila in reporte['reservas']]
        contenido.append(tabla([('Código', ''), ('Huésped', ''), ('Alojamiento', ''), ('Entrada', ''),
                                ('Noches', 'derecha'), ('Pers.', 'derecha'), ('Total', 'derecha'), ('Estado', '')],
                               filas, [0.155, 0.13, 0.165, 0.115, 0.08, 0.07, 0.135, 0.15],
                               relleno=5, total=['Total', '', '', '', entero(resumen['noches']), entero(resumen['huespedes']),
                                      pesos(resumen['ingresos']), '']))
    else:
        contenido.append(vacio('No hay reservas en este periodo.'))
    return documento(contenido, 'Reporte de {0}'.format(anfitrion['usuario']))


def pdf_general(reporte):
    resumen = reporte['resumen']
    contenido = [
        encabezado('REPORTE GENERAL', 'Anfitriones', 'Resumen de toda la plataforma', reporte),
        Spacer(1, 22),
        indicadores([tarjetas_ingresos(resumen), [
            ('Anfitriones', entero(resumen['anfitriones'])),
            ('Noches reservadas', entero(resumen['noches'])),
            ('Huéspedes alojados', entero(resumen['huespedes'])),
            ('Canceladas', entero(resumen['canceladas'])),
        ]]),
        Spacer(1, 4),
        linea_estados(reporte['estados']),
        *seccion_meses(reporte),
        *titulo_seccion('Ingresos por anfitrión', 'Ordenados por valor facturado en el periodo.'),
    ]
    if reporte['anfitriones']:
        filas = [[doble(fila['nombre'], fila['correo']), entero(fila['alojamientos']), entero(fila['reservas']),
                  entero(fila['noches']), entero(fila['huespedes']), entero(fila['canceladas']),
                  pesos(fila['ingresos'])]
                 for fila in reporte['anfitriones']]
        contenido.append(tabla([('Anfitrión', ''), ('Alojam.', 'derecha'), ('Reservas', 'derecha'),
                                ('Noches', 'derecha'), ('Huésp.', 'derecha'), ('Cancel.', 'derecha'),
                                ('Ingresos', 'derecha')],
                               filas, [0.33, 0.1, 0.1, 0.1, 0.1, 0.1, 0.17], relleno=6,
                               total=['Total', entero(resumen['alojamientos']), entero(resumen['reservas']),
                                      entero(resumen['noches']), entero(resumen['huespedes']),
                                      entero(resumen['canceladas']), pesos(resumen['ingresos'])]))
    else:
        contenido.append(vacio('Todavía no hay anfitriones registrados.'))
    return documento(contenido, 'Reporte general de anfitriones')
