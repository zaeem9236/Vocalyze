from dotenv import load_dotenv
load_dotenv()
import os, time, random, requests, json, datetime
LANGSMITH_API_KEY = os.environ.get('LANGSMITH_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
BLAND_AI_API_KEY = os.environ.get('BLAND_AI_API_KEY')
TWILIO_ENCRYPTED_KEY = os.environ.get('TWILIO_ENCRYPTED_KEY')
BLAND_AI_BASE_URL = "https://api.bland.ai"
APPWRITE_API_KEY = os.environ.get('APPWRITE_API_KEY')
APPWRITE_PROJECT_ID = os.environ.get('APPWRITE_PROJECT_ID')
APPWRITE_DATABASE_ID = os.environ.get('APPWRITE_DATABASE_ID')
APPWRITE_COLLECTION_ID = os.environ.get('APPWRITE_COLLECTION_ID')
DISCORD_WEBHOOK_ID = os.environ.get('DISCORD_WEBHOOK_ID')
DISCORD_WEBHOOK_TOKEN = os.environ.get('DISCORD_WEBHOOK_TOKEN')
ENV=os.environ.get('ENV')
os.environ["LANGSMITH_TRACING"]="true"
os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"]=LANGSMITH_API_KEY
os.environ["LANGSMITH_PROJECT"]="VOCALYZE"
os.environ["OPENAI_API_KEY"]=OPENAI_API_KEY

from prompts.call_prompt import call_prompt
from prompts.result_prompt import result_prompt
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query
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
from langsmith import Client as LangsmithClient
import uuid


# Initialize Langsmith Client
langsmith_client = LangsmithClient()
 

# Initialize & Connect to Appwrite Database
client = Client()
client.set_endpoint("https://cloud.appwrite.io/v1")  # Update with your Appwrite endpoint
client.set_project(APPWRITE_PROJECT_ID)  # Replace with your project ID
client.set_key(APPWRITE_API_KEY)  # Replace with your API Ke
database = Databases(client)
database_id = APPWRITE_DATABASE_ID
collection_id = APPWRITE_COLLECTION_ID
document_id = ''
pending_calls = 0
langsmith_logs = []


# Initialize OpenAI Chat Model
llm=ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0)


# Define the agent state
class AgentState(MessagesState):
    user_phone_number: str
    call_id: str
    call_status: str
    call_details: dict
    num_questions: str
    fetched_questions: dict
    language: str


# Define global agent state tracker
agent_state_tracker = {}


# Define global funcion to update call status
global_status_update_func = lambda: None


# Define the agent tools
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
    langsmith_logs.append({"value": {"type": type(details), "value": details}, "comment": "Call details"})
    prompt_data = {
        "num_questions": agent_state_tracker["num_questions"],
        "fetched_questions": agent_state_tracker["fetched_questions"],
        "summary": details["concatenated_transcript"],
        "country": details["variables"]["country"],
        "call_length": details["call_length"],
        "price": details["price"]
    }
    prompt = result_prompt(prompt_data)
    langsmith_logs.append({"value": prompt, "comment": "Tool prompt"})
    final_response = llm.invoke(prompt).content
    print("final_response ",prompt)
    langsmith_logs.append({"value": final_response, "comment": "Tool final result"})
    return final_response
tools = [get_call_details]


# Initialize the agent
analyzer = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,  # To see detailed logs
    max_execution_time=60, # Increase time limit in seconds
    return_intermediate_steps= True
)


# Define node for the agent workflow
def fetch_aptitude_questions(state: AgentState) -> Command[Literal["initiate_call"]]:
    return Command(
    update={"fetched_questions": random.sample(question_data, int(state['num_questions']))},
    goto="initiate_call",
    )


# Define node for the agent workflow    
def initiate_call(state: AgentState) -> Command[Literal["analyze_call_data", "__end__"]]:
    number=state['user_phone_number']
    global document_id
    global pending_calls
    document_id = ''
    pending_calls = 0
    
    is_number_exists = database.list_documents(
    database_id=database_id,
    collection_id=collection_id,
    queries=[Query.equal("number", number)]
    )
    
    if is_number_exists['total'] == 0:
      response = database.create_document(
        database_id=database_id,
        collection_id=collection_id,
        document_id="unique()",  # Generates a unique ID
        data={
          "number": number,
          "pending-calls": 2
          }
        )
      document_id = response['$id']
      pending_calls = response['pending-calls']
    else:
      document_id = is_number_exists['documents'][0]['$id']
      pending_calls = is_number_exists['documents'][0]['pending-calls']
      
    
    if pending_calls == 0:
      return Command(
          update={'call_status': 'denied', 'call_id': ''},
          goto='__end__',
      )
    
    call_status = 'queue'
    call_id = ''
    debug_mode = False
    if debug_mode:
      dummy_call_id = ""
      return Command(
          update={ "call_status": "completed", "call_id": dummy_call_id },
          goto="analyze_call_data",
      )

    import requests, json, time
    payload = {
        "phone_number": state['user_phone_number'],
        "pathway_id": None,
        "task": call_prompt(state),
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
      langsmith_logs.append({"value": {"type": type(response), "value": response}, "comment": "Bland API response"})
    if response['status'] == 'error':
      return Command(
          update={'call_status': 'failed', 'call_id': ''},
          goto='__end__',
      )
    DISCORD_WEBHOOK_URL = f"https://discord.com/api/webhooks/{DISCORD_WEBHOOK_ID}/{DISCORD_WEBHOOK_TOKEN}"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    data = {
    "content": f"📞 **Incoming Call Alert!**\n"
               f"👤 **Caller Number:** `{state['user_phone_number']}`\n"
               f"🕒 **Time:** `{timestamp}`\n"
               f"📢 **Platform:** Vocalyze\n"
               f"\n\n"
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)  # 5s timeout to prevent hanging
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Failed to send notification: {e}")
    call_id = response['call_id']
    event_url = f"{BLAND_AI_BASE_URL}/v1/event_stream/{call_id}"
    stop = False
    for log_number in range(60):  # Loop 60 times
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
      if 'Agent speech' in event['message'][:14] or 'Call connected' in event['message'][:14]:
        global_status_update_func('in_progress')
      time.sleep(5)  # Wait for 5000 millisecond
    print("last_state ", state)
    return Command(
          update={'call_status': call_status, 'call_id': call_id},
          goto=goto,
      )    


# Define node for the agent workflow
def analyze_call_data(state: AgentState):
    global agent_state_tracker
    agent_state_tracker=state
    response = analyzer({"input": f"call_id={state['call_id']}"})
    langsmith_logs.append({"value": {"type":  type(response['output']), "value": response['output']}, "comment": "Analyser response output type and value"})
    state["messages"].append(AIMessage(content=json.dumps(response['output'])))
    database.update_document(
        database_id=database_id,
        collection_id=collection_id,
        document_id=document_id,
        data={"pending-calls": (pending_calls-1) if pending_calls > 0 else 0}
    )
    return Command(
          goto="__end__",
      )
    

# Langgraph workflow
random_uuid = uuid.uuid4()
memory = MemorySaver()
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



# Define the agent function   
def agent(user_phone_num: str, num_questions: str, language: str, random_uuid, status):
    # config = {"configurable": {"thread_id": f"{random_uuid}"}}
    config = {"configurable": {"thread_id": f"dev-{random_uuid}" if ENV=='dev' else f"prod-{random_uuid}"}}
    global global_status_update_func
    global_status_update_func = status
    global_status_update_func('queue')
    response = app.invoke({"messages": "", "user_phone_number": user_phone_num, "num_questions": num_questions, "language": language},config)
    langsmith_logs.append({"value": {"full_messages":  response['messages'], "content": response['messages'][-1].content}, "comment": "Value that is causing JSONDecodeError"})
    
    # updating logs in langsmith
    run =  list(langsmith_client.list_runs(project_name=os.environ.get("LANGSMITH_PROJECT"), limit=1))    # Convert generator to a list
    # Create a feedback log entry
    for i, log in enumerate(langsmith_logs, start=1):
      langsmith_client.create_feedback(
          run_id=run[0].id,
          key=i,  # A unique key for your log
          score=None,  # No numerical score, just storing the log
          comment=log["comment"],  # The actual log message
          value=log["value"],  # The value associated with the log
      )
    
    if response['call_status'] == 'denied':
      global_status_update_func('denied')
      return {}
    
    if response['call_status'] == 'busy':
      global_status_update_func('busy')
      return {}
    
    if response['call_status'] == 'failed':
      global_status_update_func('failed')
      return {}
    
    if response['call_status'] == 'completed':
      global_status_update_func('completed')
      first_decode = json.loads(response['messages'][-1].content)
      # Second load (final dict conversion if still string)
      if isinstance(first_decode, str):
        final_dict = json.loads(first_decode)
      else:
        final_dict = first_decode
      return final_dict
      
      
    return {}