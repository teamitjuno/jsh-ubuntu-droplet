from django import template

register = template.Library()


@register.filter
def times(number):
    return range(number)


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)
