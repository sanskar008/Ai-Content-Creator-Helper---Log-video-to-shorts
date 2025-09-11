import google.generativeai as genai

# Replace with your actual Gemini API key
genai.configure(api_key="AIzaSyCAuuQRcB4VzOaIjlSCSySFcdju1jtA7bo")

model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Say hello, Gemini!")


print("Gemini response:", response.text)
