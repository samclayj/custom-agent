from openai import OpenAI
import os
import subprocess
import json

OPENAPI_API_KEY=''

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
context = []

# Open AI Specific JSON blob.
tools = [
    {
        "type": "function",
        "name": "ping",
        "description": "ping some host on the internet",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "hostname or ip.",
                },
            },
            "required": ["host"],
        },
    },
    {
        "type": "function",
        "name": "stringmod",
        "description": "custom method for modifying a string",
        "parameters": {
            "type": "object",
            "properties": {
                "stringparam": {
                    "type": "string",
                    "description": "just a string to modify and send back",
                },
            },
            "required": ["stringparam"],
        },
    }
]


def stringmod(stringparam=""):
    print(f"String Mod Call: {stringparam}")
    result = f"Wow gotta get that string: {stringparam}"
    return result

def ping(host=""):
    print(f"Ping Call: {host}")
    try:
        result = subprocess.run(
                ["ping", "-c", "5", host],
                text=True,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE)
        return result.stdout
    except Exception as e:
        return f"error: {e}"

def call(tools):
    return client.responses.create(model="gpt-5", tools=tools, input=context)

tool_functions = {
    "ping": ping,
    "stringmod": stringmod,
}

def handle_tools(tools, response):
    context.extend(response.output)
    tool_outputs = []
    needs_another_call = False

    for item in response.output:
        if item.type == "function_call":
            needs_another_call = True
            function_to_call = tool_functions.get(item.name)
            if not function_to_call:
                result = f"Error: tool '{item.name}' not found."
            else:
                arguments = json.loads(item.arguments)
                result = function_to_call(**arguments)

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": result,
            })

    if tool_outputs:
        context.extend(tool_outputs)

    return needs_another_call

def process(line):
    context.append({"role": "user", "content": line})
    response = call(tools)    
    while handle_tools(tools, response):
        response = call(tools)
    context.append({"role": "assistant", "content": response.output_text})        
    return response.output_text

while True:
    user_input = input(">> ")
    response = process(user_input)
    print(f"> {response}")
