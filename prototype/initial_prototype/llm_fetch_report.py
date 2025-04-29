import requests

# Replace with your OpenRouter API key
API_KEY = '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'
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Function to send a message to OpenRouter.ai
def send_message(messages):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "openai/gpt-3.5-turbo",  # Specify the model you want to use
        "messages": messages,
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Interactive chat loop
def chat():
    messages = []  # Stores the conversation history
    print("Welcome to the OpenRouter.ai Chat! Type 'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Add user message to the conversation history
        messages.append({"role": "user", "content": user_input})

        # Send the message to OpenRouter.ai
        bot_response = send_message(messages)
        if bot_response:
            print(f"Bot: {bot_response}")
            # Add bot response to the conversation history
            messages.append({"role": "assistant", "content": bot_response})

# Run the chat
if __name__ == "__main__":
    chat()