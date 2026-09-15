import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import Callable, Optional

from tools import get_schema, run_query
tool_map = {
    "get_schema": get_schema,
    "run_query": run_query
}

# loading API key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
system_instruction = """
            You are an expert SQL Assistant connected to a SQLite database.

            Workflow Guidelines:
            1. Schema Inspection: Inspect the schema using `get_schema` only if necessary.
            2. Query Execution: Execute read-only SQL queries using `run_query`.
            3. Error Handling: If a query fails with an error, analyze the error and retry with a corrected query.
            4. Empty Results: If a query returns empty results (no records found), do NOT repeatedly retry with speculative queries. Conclude immediately that no matching data exists in the database.
            5. Security: Never attempt data modification statements (INSERT, UPDATE, DELETE, DROP). If requested to modify data, state clearly that you only support read-only queries.
            6. Output: Always provide a concise, direct, and factual answer based strictly on the retrieved data.
            """

if not api_key:
    raise ValueError("GEMINI_API_KEY or API_KEY is not set in .env file")

client = genai.Client(api_key=api_key)

def ask_agent(user_prompt: str, on_step: Optional[Callable[[str, dict], None]] = None):
    # Create a chat session with the Gemini API. The tools are the functions that the agent can call to interact with the database.
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[get_schema, run_query],
            temperature=0.0, # Deterministic responses
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )
    )
    # Initial message to the agent to set the context
    response = chat.send_message(user_prompt)
    step = 0

    while response.function_calls and step < 5:  # Limit the number of function calls to avoid infinite loops
        step += 1
        tool_responses = []

        for function_call in response.function_calls:
            # activating callback function
            if on_step:
                on_step(function_call.name, function_call.args)

            # Execute the tool function based on the agent's request
            tool_function = tool_map.get(function_call.name)
            if not tool_function:
                result = {"error": f"Tool '{function_call.name}' not found. Available tools: {list(tool_map.keys())}"}
            else:
                result = tool_function(**function_call.args)

            # Send the result back to the agent for further processing
            tool_responses.append(
                            types.Part.from_function_response(
                            name=function_call.name,
                            response={"result": result}
                            )
                        )
        response = chat.send_message(tool_responses)

    return response.text or ""

if __name__ == "__main__":
    prompt = "What are the titles of the 5 longest songs?"
    answer = ask_agent(prompt)
    print("\n--- Final Answer ---")
    print(answer)