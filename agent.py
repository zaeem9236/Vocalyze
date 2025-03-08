from dotenv import load_dotenv
load_dotenv()
import os, time, random, requests, json
LANGSMITH_API_KEY = os.environ.get('LANGSMITH_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
BLAND_AI_API_KEY = os.environ.get('BLAND_AI_API_KEY')
TWILIO_ENCRYPTED_KEY = os.environ.get('TWILIO_ENCRYPTED_KEY')
BLAND_AI_BASE_URL = "https://api.bland.ai"


from questions import question_data
from langchain.chat_models import ChatOpenAI  # type: ignore
from langgraph.graph import MessagesState
from typing import List, Any
from langchain.agents import tool
from langchain.schema import  HumanMessage, AIMessage, SystemMessage
from langchain.agents import initialize_agent, AgentType
from langgraph.types import Command
from typing import Literal
from langgraph.graph import Graph, StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
import uuid
 


    
    
llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0)

class AgentState(MessagesState):
    user_phone_number: str
    call_id: str
    call_status: str
    call_details: dict
    num_questions: str
    fetched_questions: dict
    language: str
agent_state_tracker = {}

@tool(return_direct=True)
def get_call_details(call_id: str) -> dict:
    """
    Calculates the user's aptitude test score based on the number of correct answers.
    Args:
        call_id (str): The unique identifier for the aptitude test session.
    Returns:
        dict: A dictionary containing:
          - "score" (int): The user's aptitude test score represented as a percentage.
          - "analysis" (list): A list of dictionaries, where each dictionary contains:
              - "question" (str): The question text.
              - "correct_answer" (str): The correct answer to the question.
              - "user_answer" (str): The user's provided answer (or `"Not Answered"` if no answer was given).
              - "is_correct" (bool): True if the user's answer is correct, otherwise False.
          - "country" (str): The country where the call originated.
          - "call_length" (str): The duration of the call in seconds.
          - "price" (str): The cost of the call.
          - "lead_generated" (Boolean): Lead generated or not, based on the summary.
    """
    call_id = agent_state_tracker['call_id']
    call_details_url = f"{BLAND_AI_BASE_URL}/v1/calls/{call_id}"
    details = requests.request("GET", url=call_details_url, headers={"authorization": BLAND_AI_API_KEY,})
    details = json.loads(details.text)
    prompt_data = {
        "num_questions": agent_state_tracker["num_questions"],
        "fetched_questions": agent_state_tracker["fetched_questions"],
        "summary": details["concatenated_transcript"],
        "country": details["variables"]["country"],
        "call_length": details["call_length"],
        "price": details["price"]
    }
    prompt = f"""
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
    final_response = llm.invoke(prompt).content
    print("final_response ",prompt)
    return final_response

tools = [get_call_details]
analyzer = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,  # To see detailed logs
    max_execution_time=60, # Increase time limit in seconds
    return_intermediate_steps= True
)

def fetch_aptitude_questions(state: AgentState) -> Command[Literal["initiate_call"]]:
    return Command(
    update={"fetched_questions": random.sample(question_data, int(state['num_questions']))},
    goto="initiate_call",
    )
    
def initiate_call(state: AgentState) -> Command[Literal["analyze_call_data", "__end__"]]:
    call_status = 'queue'
    call_id = ''
    debug_mode = False
    if debug_mode:
      dummy_call_id = "e96fa339-f514-4d8c-97a9-d5231db4021f"
      return Command(
          update={ "call_status": "completed", "call_id": dummy_call_id },
          goto="analyze_call_data",
      )
    scenario_prompt = f"""Aptitude Test Knowledge Check Call Script
    Scenario: You are Alex, an AI assistant from Vocalyze Academy. You’re calling this person to ask them two quick aptitude test questions. If they don’t know the answer, provide a brief explanation. Keep the conversation friendly and engaging!
    Call Script:
    Person: Hello?
    You: Hey, this is Alex from Vocalyze Academy! Can I take a quick minute to ask you two fun aptitude test questions?
    Person: Uh, sure!
    You: Great! Let’s get started—{state['fetched_questions'][0]['question']}
    (If they answer correctly:)
    You: That’s right! {state['fetched_questions'][0]['correct_response']} Nice work!
    (If they don’t know:)
    You: No worries! {state['fetched_questions'][0]['incorrect_response']}
    You: Here’s the second one—{state['fetched_questions'][1]['question']}
    (If they answer correctly:)
    You: Exactly! {state['fetched_questions'][1]['correct_response']}
    (If they don’t know:)
    You: No problem! {state['fetched_questions'][1]['incorrect_response']}
    """
    if state['num_questions'] == 4:
      scenario_prompt = scenario_prompt + f"""You: Alright, here’s another one—{state['fetched_questions'][2]['question']}
    (If they answer correctly:)
    You: Exactly! {state['fetched_questions'][2]['correct_response']}
    (If they don’t know:)
    You: No problem! {state['fetched_questions'][2]['incorrect_response']}
    You: And here comes the last one—{state['fetched_questions'][3]['question']}
    (If they answer correctly:)
    You: Exactly! {state['fetched_questions'][3]['correct_response']}
    (If they don’t know:)
    You: No problem! {state['fetched_questions'][3]['incorrect_response']}
    """
    scenario_prompt = scenario_prompt + """You: Thanks for your time! You did great. Would you like a free guide to improve your aptitude test skills?
    (If yes, send them a resource link.)
    You: Awesome! I’ll send that over. Have a great day!
    """
    import requests, json, time
    payload = {
        "phone_number": state['user_phone_number'],
        "pathway_id": None,
        "task": scenario_prompt,
        "voice": "nat",
        "background_track": "none",
        # "first_sentence": "Hi this is AI",
        "wait_for_greeting": True,
        "block_interruptions": True,
        "interruption_threshold": 100,
        "model": "enhanced",
        "temperature": 0.7,
        "keywords": [],
        "pronunciation_guide": [{}],
        "transfer_phone_number": None,
        "transfer_list": {},
        "language": state['language'],
        "pathway_version": 123,
        "local_dialing": True,
        "voicemail_sms": {},
        # "dispatch_hours": {},
        "sensitive_voicemail_detection": True,
        "noise_cancellation": True,
        "ignore_button_press": True,
        "language_detection_period": 50,
        "language_detection_options": [],
        "timezone": "America/Los_Angeles",
        "request_data": {},
        "tools": None,
        "start_time": None,
        "voicemail_message": None,
        "voicemail_action": None,
        "retry": None,
        "max_duration": 4,
        "record": True,
        # "from": "<string>",
        "webhook": None,
        "webhook_events": ["queue", "call", "latency"],
        "metadata": {},
        "analysis_preset": None,
        "available_tags": []
    }
    headers = {
        "authorization": BLAND_AI_API_KEY,
        "encrypted_key": TWILIO_ENCRYPTED_KEY,
        "Content-Type": "application/json",
    }
    if not debug_mode:
      response = requests.request("POST", url = f"{BLAND_AI_BASE_URL}/v1/calls", json=payload, headers=headers)
      response = json.loads(response.text)
    if response['status'] == 'error':
      return Command(
          update={'call_status': 'failed', 'call_id': ''},
          goto='__end__',
      )  
    call_id = response['call_id']
    event_url = f"{BLAND_AI_BASE_URL}/v1/event_stream/{call_id}"
    stop = False
    for log_number in range(60):  # Loop 9 times
      events = requests.request("GET", url=event_url, headers=headers)
      print('event log. ', events, events.text)
      events = json.loads(events.text)
      if events['event_stream_data']:
        events = events['event_stream_data'][-4:]
      if len(events) == 0:
        events = []
      for event in events:
        if 'Call duration & price:' in event['message']:
          if 'Call duration & price: 0s, $0' in event['message']:
            call_status = 'busy'
            print(f'busy response in {log_number*5} secs')
            goto ="__end__"
            stop = True
          else:
            call_status = 'completed'
            print(f'completed response in {log_number*5} secs')
            goto="analyze_call_data"
            stop = True
            break
      if stop:
        break
      time.sleep(5)  # Wait for 5000 millisecond
    print("last_state ", state)
    return Command(
          update={'call_status': call_status, 'call_id': call_id},
          goto=goto,
      )    

def analyze_call_data(state: AgentState):
    global agent_state_tracker
    agent_state_tracker=state
    response = analyzer({"input": f"call_id={state['call_id']}"})
    state["messages"].append(AIMessage(content=json.dumps(response['output'])))
    return Command(
          goto="__end__",
      )
    
random_uuid = uuid.uuid4()
memory = MemorySaver()
#Graph
workflow = StateGraph(AgentState)
workflow.add_node("fetch_aptitude_questions", fetch_aptitude_questions) # adding node
workflow.add_node("initiate_call", initiate_call) # adding node
workflow.add_node("analyze_call_data", analyze_call_data) # adding node
workflow.add_node("tools", ToolNode(tools)) # adding node
workflow.add_edge(START, "fetch_aptitude_questions") # adding edges
workflow.add_conditional_edges( # adding conditional edges
    "analyze_call_data",
    tools_condition,
)
workflow.add_edge("tools", 'analyze_call_data') # adding edges
app = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": f"{random_uuid}"}}


    
def agent(user_phone_num: str, num_questions: str, language: str, status):
    
    response = app.invoke({"messages": "", "user_phone_number": user_phone_num, "num_questions": num_questions, "language": language},config)
    
    if response['call_status'] == 'busy':
      status["call_status"] = 'busy'
      return {}
    
    if response['call_status'] == 'failed':
      status["call_status"] = 'failed'
      return {}
    
    if response['call_status'] == 'completed':
      status['call_status'] = 'completed'
      first_decode = json.loads(response['messages'][1].content)
      # Second load (final dict conversion if still string)
      if isinstance(first_decode, str):
        final_dict = json.loads(first_decode)
      else:
        final_dict = first_decode
      return final_dict
      
      
    return {}