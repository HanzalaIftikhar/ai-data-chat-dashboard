from src.data_processing import process_uploaded_file, generate_summary
from src.ai_engine import ask_question


class FakeUploadedFile:
    def __init__(self, path):
        self.name = path
        self._file = open(path, "rb")

    def read(self, *args):
        return self._file.read(*args)

    def seek(self, *args):
        return self._file.seek(*args)


f = FakeUploadedFile("sample_data/superstore.csv")
df, detected = process_uploaded_file(f)
summary = generate_summary(df)

print("--- Summary ---")
print(summary)

question = "How is my business doing overall?"
print(f"\n--- Asking Gemini: '{question}' ---")

answer = ask_question(df, summary, question)
print("\nGemini's Answer:")
print(answer)