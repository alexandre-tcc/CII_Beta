# fonts
title_size = 26
body_size = 20

# styles
button_style = {'margin': '20px 20px 20px 20px', 'fontSize': 18, 'font-family': 'sans-serif'}

orange_tcc = '#FFA41B'
blue_tcc = '#3384BA'


def format_string(input_string):
    formatted_string = ''
    for char in input_string:
        if char.isupper():
            formatted_string += ' '
        formatted_string += char
    formatted_string = formatted_string.replace('_', ' ')
    formatted_string = formatted_string.strip()
    formatted_string = formatted_string.title()
    return formatted_string
