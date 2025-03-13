def result_prompt(prompt_data):
    return f"""
     Your task is to calculate the user's score based on the provided input data and generate a detailed analysis of their performance.
      ### Input:
      Below is the data you will receive:
      {prompt_data}
      ### Explanation:
      1. **num_questions** (string): Total number of questions asked during the call.
      2. **fetched_questions** (list of dictionaries): Each dictionary contains:
         - **question** (string): The text of the question.
         - **correct_answer** (string): The correct answer to the question.
      3. **summary** (string): A summary of the call interaction, which includes:
         - The user's responses.
         - Which answers were correct or incorrect.
         - Any corrections provided by the agent.
      4. **country** (string): The country where the call originated.
      5. **call_length** (string): The duration of the call in seconds.
      6. **price** (string): The cost of the call.
      7. **lead_generated** (Boolean): Lead generated or not, based on the summary.
      ### Your Task:
      1. Extract the **user's answers** from the **summary**.
      2. Compare the user's answer with the **correct_answer** from **fetched_questions**.
      3. For each question, create an **analysis object** with the following structure:
         - **question**: The question text.
         - **correct_answer**: The correct answer.
         - **user_answer**: The extracted user's answer.
         - **is_correct**: True if the user's answer is correct, otherwise False.
      4. Calculate the **score** using this formula:
      (score = (Correct Answers / {prompt_data['num_questions']}) * 100)
      5. Set **lead_generated** to True if the user's response shows interest toward the question **"Would you like a free guide to improve your aptitude test skills"** or similar wording. Otherwise, set **lead_generated** to False.
      6. Always return the output in the following dictionary format:
      {{
        "score": "<calculated_score>",
        "analysis": [
          {{
            "question": "<question_text>",
            "correct_answer": "<correct_answer>",
            "user_answer": "<user_answer>",
            "is_correct": "<True_or_False>"
          }}
        ],
        "country": "<country>",
        "call_length": "<call_length>",
        "price": "<price>",
        "lead_generated": "<True_or_False>"
      }}
      ### Important Rules:
      - The **output must always be a dictionary** with the keys: `"score"`, `"analysis"`, `"country"`, `"call_length"`, `"price"`, and `"lead_generated"`.
      - If no answer is found for a question in the summary, set `"user_answer"` to `"Not Answered"` and `"is_correct"` to False.
      - Always calculate the result based on the **fetched_questions** field. Ignore questions from the summary if not present in **fetched_questions**.
      - Be consistent with the **JSON format**.
      """