
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError

from io import BytesIO
import os
import io
import re
import base64
import tempfile

import xmlrpc.client

from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)

# =============================================================================
# Generación del PDF
# =============================================================================

def _image_flowable(b64_image_data, size):
    """Decodifica una imagen base64 de Odoo a un flowable de reportlab.
    Devuelve None si no hay imagen."""
    if not b64_image_data:
        return None
    try:
        img_bytes = base64.b64decode(b64_image_data)
        img_buffer = io.BytesIO(img_bytes)
        return Image(img_buffer, width=size, height=size)
    except Exception:
        return None


def simple_text_to_paragraph(text, style):
    if not text:
        return None
    escaped = escape(text)
    content = escaped.replace("\n", "<br/>")
    return Paragraph(content, style)

GROUP_IMAGE_SIZE_MM = 60

class EscanortCatalogo(models.Model):
    _name = 'escanort.catalogo'
    _description = 'escanort.catalogo'

    name = fields.Char('Nombre')
    date = fields.Date('Fecha',default=fields.Date.today())
    catalog_file = fields.Binary('Archivo Catalogo')
    pricelist_id = fields.Many2one('product.pricelist',string='Lista de precios')

    def build_catalog(self):
        groups = self.env['product.group'].search([])

        groups_with_products = []
        for group in groups:
            product_ids = group.product_ids
            groups_with_products.append({
                "name": group.name,
                "description": group.description,
                "image": group.image,
                "products": group.product_ids,
            })

        self.build_pdf(groups_with_products)

    
    def build_pdf(self, groups_with_products):
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)  # mkstemp opens the file descriptor; close it if you're not using it directly

        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            topMargin=30 * mm,
            bottomMargin=15 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )

        styles = getSampleStyleSheet()
        elements = []

        if self.pricelist_id:
            product_table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),  # precio alineado a la derecha
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        else:
            product_table_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                #("ALIGN", (1, 1), (1, -1), "RIGHT"),  # precio alineado a la derecha
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])

        img_size = GROUP_IMAGE_SIZE_MM * mm

        # Ancho total disponible = pageWidth - márgenes izq/der
        content_width = doc.width
        img_col_width = img_size + 6 * mm
        text_col_width = content_width - img_col_width

        for i, group in enumerate(groups_with_products):

            img = _image_flowable(group.get("image"), img_size)
            #import pdb;pdb.set_trace()

            text_flow = [Paragraph(group.get("name") or "(sin nombre)", styles["Heading1"])]
            if group.get("description"):
                #description = sanitize_odoo_html(group["description"])
                #text_flow.append(Spacer(1, 2 * mm))
                #text_flow.append(Paragraph(group["description"], styles["Normal"]))
                text_flow.append(Spacer(1, 2 * mm))
                text_flow.append(simple_text_to_paragraph(group.get("description"), styles["Normal"]))

            header_row = [[img if img else "", text_flow]]
            header_table = Table(header_row, colWidths=[img_col_width, text_col_width])
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 6 * mm))

            products = group.get("products")

            header_style = ParagraphStyle(
                'header_style',
                parent=styles['Normal'],
                textColor=colors.white,   # ← agregá o cambiá esta línea
                fontName='Helvetica-Bold',
                fontSize=10,
                leading=12
            )

            if products:
                if self.pricelist_id:
                    data = [[Paragraph("Código",header_style), Paragraph("Precio",header_style),Paragraph("Peldaños",header_style),Paragraph("Altura Cerrada",header_style),Paragraph("Altura Extendida",header_style),Paragraph("Ancho",header_style),Paragraph("Cruce",header_style),Paragraph("Peso",header_style)]]
                else:
                    data = [[Paragraph("Código",header_style), Paragraph("Peldaños",header_style),Paragraph("Altura Cerrada",header_style),Paragraph("Altura Extendida",header_style),Paragraph("Ancho",header_style),Paragraph("Cruce",header_style),Paragraph("Peso",header_style)]]
                for p in products:
                    if self.pricelist_id:
                        price = self.pricelist_id._get_product_price(
                            product=p,
                            quantity=1.0,
                        )
                        data.append([
                            p.default_code or "",
                            #f"{prod.list_price, 0.0):,.2f}",
                            f"${price:,.2f}",
                            p.steps or "-",
                            p.alto or "-",
                            p.alto1 or "-",
                            #p.alto2 or "-",
                            p.ancho or "-",
                            p.cruce or "-",
                            p.peso or "-",
                        ])
                    else:
                        data.append([
                            p.default_code or "",
                            p.steps or "-",
                            p.alto or "-",
                            p.alto1 or "-",
                            #p.alto2 or "-",
                            p.ancho or "-",
                            p.cruce or "-",
                            p.peso or "-",
                        ])
                if self.pricelist_id:
                    table = Table(data, colWidths=[25 * mm, 25 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm], repeatRows=1)
                else:
                    table = Table(data, colWidths=[25 * mm, 15 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm], repeatRows=1)
                table.setStyle(product_table_style)
                elements.append(table)
            else:
                elements.append(Paragraph("Sin productos relacionados.", styles["Italic"]))

            if i < len(groups_with_products) - 1:
                elements.append(PageBreak())

        doc.build(elements, onFirstPage=self.add_header_footer, onLaterPages=self.add_header_footer)
        f = open(path, 'rb') 
        pdf_data = f.read()
        encoded_data = base64.b64encode(pdf_data)
        self.write({'catalog_file': encoded_data})

    def add_header_footer(self, canvas, doc):
        canvas.saveState()

        company = self.env.company
        # --- Logo ---
        if company.logo:
            logo_data = base64.b64decode(company.logo)
            logo_img = ImageReader(BytesIO(logo_data))

            # mantener proporción del logo
            img_w, img_h = logo_img.getSize()
            aspect = img_h / img_w
            display_w = 30 * mm
            display_h = display_w * aspect

            canvas.drawImage(
                logo_img,
                20 * mm, A4[1] - 15 * mm - display_h,
                width=display_w, height=display_h,
                preserveAspectRatio=True, mask='auto'
            )

        # --- Texto del header, al lado o debajo del logo ---
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(55 * mm, A4[1] - 15 * mm, company.name)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(55 * mm, A4[1] - 20 * mm, company.street or "" + ", " +  company.city)

        canvas.setStrokeColor("#bdc3c7")
        canvas.line(20 * mm, A4[1] - 25 * mm, A4[0] - 20 * mm, A4[1] - 25 * mm)

        # --- Footer ---
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20 * mm, 15 * mm, self.env.company.website)
        canvas.drawRightString(A4[0] - 20 * mm, 15 * mm, "Página %s - %s"%(doc.page,self.date))

        canvas.restoreState()


