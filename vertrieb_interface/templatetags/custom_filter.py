from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name='format_number')
def format_number(value):
    try:
        # Convert the value to a float, then format with thousand separator
        return "{:,.1f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
    except ValueError:
        # If conversion to float fails, return original value
        return value
    
@register.filter(name='format_price')
def format_price(value):
    try:
        # Convert the value to a float, then format with thousand separator
        formatted_price = "{:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted_price} €"
    except ValueError:
        # If conversion to float fails, return original value
        return value