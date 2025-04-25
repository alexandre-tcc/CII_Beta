import openai
import os
import time



def set_api_key():
    return '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'


def gpt_suppliers(name):
    openai.api_key = set_api_key()
    content = f'provide me with the list of suppliers of {name}, just the list no extra text'
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            {"role": "user", "content": "provide me with the list of suppliers of ametek, just the list no extra text"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply


def gpt_cycles(cycles_, name):
    # Set API key
    openai.api_key = set_api_key()

    # Perform the API call
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',  # Specify the GPT model
            messages=[
                {"role": "system",
                 "content": "You are an expert analyst. Provide concise yet thorough insights based on the user's prompt."},
                {"role": "user", "content": f"{name} has {cycles_} cycles. Provide an analysis based on this data. "
                                            "Your analysis should include critical insights, acknowledging any potential problems or areas for improvement, "
                                            "while also highlighting positive aspects or strengths. Do not redefine any terms or data descriptions. "
                                            "Focus only on providing insights from the data given, where 'last_xxx' is the most recent value, "
                                            "'avg_xxx_3y' is the 3-year average, and 'avg_xxx' is the all-time average."}
            ]
        )

        # Access the generated response
        reply = response['choices'][0]['message']['content'].strip()
        return reply

    except Exception as e:
        return f"An error occurred: {e}"


def gpt_inv_cash(inv_cash_, name):
    openai.api_key = set_api_key()

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            {"role": "system", "content": "give me a answer without redefining the terms used in the prompt"},
            {"role": "user",
             "content": "I encourage you to have negative commments if possible, " + name + " has, " + str(
                 inv_cash_) + " what insight can I extract from this, where last_xxx is last value, avg_xxx_3y is the average in the last 3 years and avg_xxx is the all time average, we are talking about cash and inventory here"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply


def gpt_inv_cash(inv_cash_, name):
    openai.api_key = set_api_key()

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            {"role": "system", "content": "give me a answer without redefining the terms used in the prompt"},
            {"role": "user",
             "content": "I encourage you to have negative commments if possible, " + name + " has, " + str(
                 inv_cash_) + " what insight can I extract from this, where last_xxx is last value, avg_xxx_3y is the average in the last 3 years and avg_xxx is the all time average, we are talking about cash and inventory here, more than 200 words"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply


def gpt_suppliers(company):
    time.sleep(61)
    openai.api_key = set_api_key()

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            # {"role": "user", "content": f"please list me the known main 15 suppliers of {company} your response should be in this format: [['SupplierA','ticker SupplierA','<Main supply from> SupplierA'],['SupplierB','ticker SupplierB','<Main supply from> SupplierB'],...] Don't include any company that doesn't have a ticker, don't fill this list with fake suppliers, i.e all suppliers should be actual companies, don't add any '\n' to your response"},
            {"role": "user",
             "content": f"please list me the known main 15 suppliers of {company} your response should look like this: [['MRC Global', 'MRC', 'Global integrated products distribution'], ['DXP Enterprises', 'DXPE', 'Focused on providing quality products and services'], ['Praxair', 'PX', 'Industrial gases']] Don't include any company that doesn't have a ticker, don't fill this list with fake suppliers, i.e all suppliers should be actual companies, don't add any '\n' to your response"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply.replace('\n', '')


def gpt_banks(company):
    time.sleep(61)
    openai.api_key = set_api_key()

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            {"role": "user", "content": f"Please list me the banks engaged with {company}"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply



def gpt_suppliers2(name):
    openai.api_key = set_api_key()
    content = f'provide me with the list of suppliers of {name}, just the list no extra text'
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',  # Specify the GPT-3.5 Turbo model
        messages=[
            {"role": "user", "content": "provide me with the list of suppliers of ametek, just the list no extra text"},
        ]
    )

    # Access the generated response
    reply = response.choices[0].message.content.strip()
    return reply

if __name__ == "__main__":
    print(gpt_inv_cash('1456,789,456', 'Medtronic'))