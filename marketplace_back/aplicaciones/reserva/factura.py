from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TINTA = colors.HexColor('#0e111b')
PROFUNDO = colors.HexColor('#f6f8fd')
COBALTO = colors.HexColor('#12244f')
BORDE = colors.HexColor('#dde3f0')
BORDE_SUAVE = colors.HexColor('#ebeef6')
CUARZO = colors.white
CENIZA = colors.HexColor('#6b7080')
BRUMA = colors.HexColor('#3c4150')
LILA = colors.HexColor('#85a6e9')
AURORA = colors.HexColor('#625fff')
AZUL = colors.HexColor('#305fbd')
AMBAR = colors.HexColor('#9a6100')
FONDO_AMBAR = colors.HexColor('#fff1d6')
ROJO = colors.HexColor('#b3261e')
FONDO_ROJO = colors.HexColor('#ffe4e7')

ANCHO = letter[0] - 4 * cm - 12
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
         'octubre', 'noviembre', 'diciembre']
MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def estilo(nombre, **opciones):
    return ParagraphStyle(nombre, **{'fontName': 'Helvetica', 'fontSize': 10, 'leading': 14,
                                     'textColor': TINTA, **opciones})


LOGO = estilo('logo', fontName='Helvetica-Bold', fontSize=13, leading=13)
EMPRESA = estilo('empresa', fontSize=9, textColor=CENIZA)
ETIQUETA = estilo('etiqueta', fontName='Helvetica-Bold', fontSize=7, leading=10, textColor=CENIZA)
ETIQUETA_ACENTO = estilo('etiqueta_acento', fontName='Helvetica-Bold', fontSize=7, leading=10, textColor=AZUL)
ETIQUETA_DERECHA = estilo('etiqueta_derecha', fontName='Helvetica-Bold', fontSize=7, leading=10,
                          textColor=CENIZA, alignment=TA_RIGHT)
NUMERO = estilo('numero', fontName='Helvetica-Bold', fontSize=24, leading=28, alignment=TA_RIGHT)
FECHA = estilo('fecha', fontSize=9, textColor=CENIZA, alignment=TA_RIGHT)
VALOR = estilo('valor')
SECUNDARIO = estilo('secundario', fontSize=9, leading=13, textColor=CENIZA)
TITULO = estilo('titulo', fontName='Helvetica-Bold', fontSize=15, leading=20)
CELDA = estilo('celda', textColor=BRUMA)
CELDA_DERECHA = estilo('celda_derecha', alignment=TA_RIGHT)
TOTAL = estilo('total', fontSize=11, leading=14, textColor=LILA)
TOTAL_VALOR = estilo('total_valor', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=CUARZO,
                     alignment=TA_RIGHT)


def pesos(valor):
    entero = Decimal(valor).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return '$ ' + '{0:,}'.format(int(entero)).replace(',', '.')


def fecha(valor):
    return '{0} de {1} de {2}'.format(valor.day, MESES[valor.month - 1], valor.year)


def fecha_corta(valor):
    return '{0} {1} {2}'.format(valor.day, MESES_CORTOS[valor.month - 1], valor.year)


def texto(valor, estilo_parrafo=VALOR):
    return Paragraph(escape(str(valor)), estilo_parrafo)


def bloque(contenido, fondo, borde, relleno=(16, 14)):
    tabla = Table([[contenido]], colWidths=[ANCHO])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), fondo), ('BOX', (0, 0), (-1, -1), 0.8, borde),
        ('ROUNDEDCORNERS', [10] * 4),
        ('LEFTPADDING', (0, 0), (-1, -1), relleno[0]), ('RIGHTPADDING', (0, 0), (-1, -1), relleno[0]),
        ('TOPPADDING', (0, 0), (-1, -1), relleno[1]), ('BOTTOMPADDING', (0, 0), (-1, -1), relleno[1]),
    ]))
    return tabla


def sin_relleno(tabla):
    tabla.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                               ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    return tabla


def insignia(factura):
    anulada = factura.estado == factura.Estado.ANULADA
    color = ROJO if anulada else AMBAR
    tabla = Table([[Paragraph('<font size="9">&#9679;</font>  ' + ('Anulada' if anulada else 'Pendiente de pago'),
                              estilo('insignia', fontName='Helvetica-Bold', fontSize=8, leading=10,
                                     alignment=TA_CENTER, textColor=color))]],
                  colWidths=[3.6 * cm], hAlign='RIGHT')
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), FONDO_ROJO if anulada else FONDO_AMBAR), ('ROUNDEDCORNERS', [8] * 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tabla


def encabezado(factura):
    tabla = Table([[
        [Paragraph('MARKET<br/><font color="#305fbd">PLACE</font>', LOGO), Spacer(1, 8), Paragraph('Inversiones LR', EMPRESA)],
        [Paragraph('FACTURA', ETIQUETA_DERECHA), Paragraph(escape(factura.numero), NUMERO),
         Paragraph(fecha(timezone.localtime(factura.fecha_generacion)), FECHA), Spacer(1, 10),
         insignia(factura)],
    ]], colWidths=[ANCHO / 2, ANCHO / 2])
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 22), ('LINEBELOW', (0, 0), (-1, 0), 0.6, BORDE),
    ]))
    return tabla


def partes(factura, publicacion):
    cliente = [Paragraph('FACTURADO A', ETIQUETA), Spacer(1, 6), texto(factura.cliente_nombre),
               texto(factura.cliente_correo, SECUNDARIO)]
    alojamiento = [Paragraph('ALOJAMIENTO', ETIQUETA), Spacer(1, 6), texto(publicacion.titulo),
                   texto('{0}, {1}'.format(publicacion.direccion, publicacion.ciudad), SECUNDARIO),
                   texto('Anfitrión: {0}'.format(publicacion.anfitrion.get_full_name()), SECUNDARIO)]
    tabla = Table([[cliente, alojamiento]], colWidths=[ANCHO * 0.42, ANCHO * 0.58])
    tabla.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 22), ('BOTTOMPADDING', (0, 0), (-1, -1), 22),
    ]))
    return tabla


def estancia(reserva):
    datos = [('RESERVA', reserva.codigo), ('ENTRADA', fecha_corta(reserva.fecha_entrada)),
             ('SALIDA', fecha_corta(reserva.fecha_salida)), ('NOCHES', reserva.noches),
             ('HUÉSPEDES', reserva.huespedes)]
    interior = Table([[[Paragraph(etiqueta, ETIQUETA_ACENTO), Spacer(1, 5), texto(valor)] for etiqueta, valor in datos]],
                     colWidths=[(ANCHO - 32) * parte for parte in (0.24, 0.22, 0.22, 0.14, 0.18)])
    return bloque(sin_relleno(interior), PROFUNDO, BORDE)


def filas_detalle(reserva):
    filas = [(texto('{0} noches x {1}'.format(reserva.noches, pesos(reserva.precio_noche)), CELDA),
              pesos(reserva.precio_base))]
    if reserva.descuento:
        filas.append((texto('Descuento por estancia larga', CELDA), '- ' + pesos(reserva.descuento)))
    if reserva.tarifa_limpieza:
        filas.append((texto('Tarifa de limpieza', CELDA), pesos(reserva.tarifa_limpieza)))
    for servicio in reserva.servicios:
        filas.append((texto(servicio['nombre'], CELDA), pesos(servicio['precio'])))
    subtotal = reserva.precio_base - reserva.descuento + reserva.tarifa_limpieza + reserva.total_servicios
    filas.append((texto('Subtotal', CELDA), pesos(subtotal)))
    filas.append((texto('Tarifa de servicio ({0:f} %)'.format(reserva.porcentaje_tarifa_servicio.normalize()),
                        CELDA), pesos(reserva.tarifa_servicio)))
    return filas


def detalle(factura, reserva):
    filas = [[Paragraph('CONCEPTO', ETIQUETA), Paragraph('VALOR', ETIQUETA_DERECHA)]]
    filas += [[concepto, Paragraph(valor, CELDA_DERECHA)] for concepto, valor in filas_detalle(reserva)]
    interior = Table(filas, colWidths=[(ANCHO - 32) * 0.72, (ANCHO - 32) * 0.28])
    interior.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, BORDE), ('LINEBELOW', (0, 1), (-1, -2), 0.5, BORDE_SUAVE),
    ]))
    total = Table([[Paragraph('Total a pagar', TOTAL), Paragraph(pesos(factura.total), TOTAL_VALOR)]],
                  colWidths=[(ANCHO - 36) / 2] * 2)
    return [bloque(interior, PROFUNDO, BORDE, relleno=(16, 6)), Spacer(1, 12),
            bloque(sin_relleno(total), COBALTO, COBALTO, relleno=(18, 18))]


def franja(lienzo, documento):
    ancho, alto = documento.pagesize
    partes_franja = 120
    lienzo.saveState()
    for paso in range(partes_franja):
        lienzo.setFillColor(colors.linearlyInterpolatedColor(AZUL, AURORA, 0, partes_franja - 1, paso))
        lienzo.rect(ancho * paso / partes_franja, alto - 6, ancho / partes_franja + 0.5, 6, stroke=0, fill=1)
    lienzo.restoreState()


def pie(lienzo, documento):
    izquierda = documento.leftMargin + 6
    lienzo.saveState()
    lienzo.setStrokeColor(BORDE)
    lienzo.setLineWidth(0.6)
    lienzo.line(izquierda, 1.6 * cm, izquierda + ANCHO, 1.6 * cm)
    lienzo.setFont('Helvetica', 8)
    lienzo.setFillColor(CENIZA)
    lienzo.drawString(izquierda, 1.15 * cm, 'Marketplace de Alojamientos · Inversiones LR')
    lienzo.drawRightString(izquierda + ANCHO, 1.15 * cm, documento.title)
    lienzo.setStrokeColor(AZUL)
    lienzo.setLineWidth(2)
    lienzo.line(izquierda, 1.6 * cm, izquierda + 40, 1.6 * cm)
    lienzo.restoreState()


def pagina(lienzo, documento):
    franja(lienzo, documento)
    pie(lienzo, documento)


def generar_pdf(factura):
    reserva = factura.reserva
    contenido = [
        encabezado(factura),
        partes(factura, reserva.publicacion),
        estancia(reserva),
        Spacer(1, 28),
        Paragraph('Detalle', TITULO),
        Spacer(1, 10),
        *detalle(factura, reserva),
    ]
    salida = BytesIO()
    SimpleDocTemplate(salida, pagesize=letter, title='Factura {0}'.format(factura.numero),
                      author='Marketplace de Alojamientos', leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=2.2 * cm).build(contenido, onFirstPage=pagina,
                                                                      onLaterPages=pagina)
    return salida.getvalue()
