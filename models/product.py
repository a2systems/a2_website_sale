
import anthropic
from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError

class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'product.group'

    name = fields.Char('Nombre')
    description = fields.Text('Descripción')
    image = fields.Binary('Imagen')
    product_ids = fields.One2many(comodel_name='product.template',inverse_name='product_group_id',string='Productos')

class ProductTemplate(models.Model):
    _inherit = "product.template"

    ai_description_generated = fields.Boolean("Descripción generated con AI", default=False)
    so_description_sale = fields.Html('Descripción para website')
    product_group_id = fields.Many2one('product.group',string='Grupo de productos')
    steps = fields.Char('Peldaños')
    alto = fields.Char('Alto')
    alto1 = fields.Char('Alto 1')
    alto2 = fields.Char('Alto 2')
    ancho = fields.Char('Ancho')
    cruce = fields.Char('Cruce')
    peso = fields.Char('Peso')


    def action_generate_description(self):
        self.ensure_one()
        api_key = self.env["ir.config_parameter"].sudo().get_param("anthropic.api_key")
        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = """Eres un redactor experto en copywriting para ecommerce. Te daré únicamente el nombre de un producto, y debes generar una descripción de producto completa, persuasiva y formateada en HTML, lista para pegar en la página de un producto de una tienda online.

Nombre del producto: {nombre_producto}

Instrucciones:
1. Infiere la categoría más probable del producto, el público objetivo y los principales puntos de venta basándote únicamente en el nombre. Si el nombre es ambiguo, haz suposiciones razonables y mantente consistente con ellas durante todo el texto.
2. Escribe en un tono persuasivo, enfocado en beneficios, adecuado para compradores online — claro, conciso y fácil de escanear visualmente.
3. Estructura el resultado usando el siguiente formato HTML:

<div class="product-description">
  <p>[Párrafo introductorio breve y atractivo - 2-3 oraciones destacando la principal propuesta de valor]</p>

  <h3>Características principales</h3>
  <ul>
    <li>[Característica 1 - enfocada en el beneficio]</li>
    <li>[Característica 2 - enfocada en el beneficio]</li>
    <li>[Característica 3 - enfocada en el beneficio]</li>
    <li>[Característica 4 - enfocada en el beneficio]</li>
    <li>[Característica 5 - enfocada en el beneficio]</li>
  </ul>

  <h3>Por qué te encantará</h3>
  <p>[Párrafo que expande los beneficios emocionales/prácticos, abordando un problema que resuelve]</p>

  <h3>Especificaciones</h3>
  <ul>
    <li><strong>[Nombre de la especificación]:</strong> [Valor]</li>
    <li><strong>[Nombre de la especificación]:</strong> [Valor]</li>
  </ul>

  <p><em>[Línea de cierre opcional - urgencia, garantía o llamado a la acción]</em></p>
</div>

4. Devuelve únicamente el código HTML — sin comentarios adicionales, sin bloques de código markdown, sin explicaciones antes o después.
5. Mantén una extensión adecuada para una ficha de producto de ecommerce (aproximadamente 150-250 palabras de texto visible, sin contar las etiquetas)."""

       
        message = client.messages.create(
            model="claude-sonnet-4-6",   # swap for another model string if you prefer
            max_tokens=300,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Nombre del producto: {self.name}\n\nEscribe la descripción del producto.",
                }
            ],
        )
        res =  "".join(block.text for block in message.content if block.type == "text")
        #raise ValidationError(res)

        self.write({
             "so_description_sale": res,
             "ai_description_generated": True,
             })

            #except Exception as e:
            #    raise UserError(f"Error generando descripción con IA: {e}")
