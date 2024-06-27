from fastapi import FastAPI
from pydantic import BaseModel
import logging
from agent_modules.agent_settings import *

# FastAPI
app = FastAPI()

import logging
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("output.log"), logging.StreamHandler(sys.stdout)])
logging.getLogger("httpx").setLevel(logging.WARNING)

# 표준 출력 리디렉션
class LoggerWriter:
    def __init__(self, level):
        self.level = level
        self.buffer = ''

    def write(self, message):
        if message != '\n': 
            self.buffer += message
        if self.buffer.endswith('\n'):
            self.level(self.buffer.strip())
            self.buffer = ''

    def flush(self):
        if self.buffer:
            self.level(self.buffer.strip())
            self.buffer = ''

    def isatty(self):
        return False

sys.stdout = LoggerWriter(logging.info)
sys.stderr = LoggerWriter(logging.error)

# Pydantic Type Class
class NPC_Chat(BaseModel):
    participant : list[str] 
    time : str
    place : str


class User_Chat(BaseModel) : 
    npc : str
    time : str
    place : str
    UUID : str
    message : str

class User_Chat_END(BaseModel):
    UUID : str


class Time(BaseModel):
    time : str

# Endpoints
@app.post("/npc_chat")
async def npc_chat(item : NPC_Chat):
    participant = item.participant
    time = convert_time(item.time)
    place = item.place
    turns = 0
    answer = f"{participant[1]} said Hello! {participant[0]}"
    agent_1 = participant[0]
    agent_2 = participant[1]
    chat_history = [f"{agent_1} said, Hi! {agent_2} How is it going?"]
    while turns < 10 :
        break_dialogue = False
        stay_in_dialogue, answer = Agents[agent_2].npc_dialogue(agent, chat_history, now=time, place=place)
        chat_history.append(answer)
        if not stay_in_dialogue:
            break_dialogue = True
        if break_dialogue:
            break
        stay_in_dialogue, answer = Agents[agent_1].npc_dialogue(agent, chat_history, now=time, place=place)
        chat_history.append(answer)
        if not stay_in_dialogue:
            break_dialogue = True
        if break_dialogue:
            break
        turns += 1
    for agent in participant :
        Agents[agent].calc_friendship(chat_history, now=time)

    return {"status" : "OK"}

@app.post("/user_chat")
async def user_chat(item : User_Chat):
    time = convert_time(item.time)
    message = f"User : f{item.message}"
    _, return_message = Agents[item.npc].dialogue(message, time, item.place)
    return_message = return_message.replace(f"{item.npc} said", "")
    return {"message" : return_message}


@app.post("/user_chat_end")
async def chat_end(item : User_Chat_END):
    print(item)
    return {"status" : "OK"}

@app.post("/time")
async def time(item : Time):
    time = convert_time(item.time)
    hour = time.strftime("%H:%M")
    time_table = []
    for agent in Agents :
        if hour == "00:00" :
            Agents[agent].make_daily_plan(time)
        Agents[agent].make_event(time)
        Agents[agent].change_status(time)
        time_table.append({agent : Agents[agent].plan[hour]})
    return {"plan" :time_table}
    
if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)