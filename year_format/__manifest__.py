{
    "name": "Year Widget",
    "version": "1.0",
    "category": "Widget",
    "author": "JL",
    "website": "http://www.jl-odoo.me",
    "sequence": 10,
    "summary": """
        Feature:
        - Year widget for list view and form view,
            in case it is Integer or Float field

        How to use:
        - Adding widget="year" attribute for your Integer field on view
        Ex: <field name="integer_year" widget="year" />
    """,
    "data": ["views/year_format_view.xml"],
    "qweb": ["static/src/xml/year_widget.xml"],
    "images":["images/module_image.png"],
    "installable": True,
    "application": True,
    "license": "OPL-1",
}
