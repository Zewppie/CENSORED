import maritalk
import telebot
from dotenv import load_dotenv
import os


prompt = """Você é um bot que filtra se uma mensagem \
é ofensiva ou não, se possui preconceitos ou age com \
mal caráter em um grupo.

Leia a mensagem a seguir e responda "Sim" se você detectar algo ofensivo, \
preconceituoso ou mal intencionado na mensagem, \
ou "Não" caso contrário. 
E não diga absolutamente nada além disso, NADA ALÉM DISSO.

Mensagem: Odeio negros.
Resposta: Sim

Mensagem: Eu gosto de batata frita.
Resposta: Não

Mensagem: Oi
Resposta: Não

Mensagem: Se mata!
Resposta: Sim

Mensagem: O nazismo foi errado
Resposta: Não

Mensagem: Porra
Resposta: Sim

Mensagem: Negros são marginalizados pelo governo
Resposta: Não

Mensagem:
"""

class Group:
    def __init__(self, chat_id: int):
        global prompt

        self.chat_id = chat_id
        self.prompt = prompt
        self.esperando_resposta = False


groups: list[Group] = []


def get_chat(chat_id: int) -> Group or None:
    for group in groups:
        if group.chat_id == chat_id:
            return group
    return None


if __name__ == "__main__":
    load_dotenv()

    CHAVE_MARITACA = os.getenv("CHAVE_MARITACA")
    CHAVE_TELEGRAM = os.getenv("CHAVE_TELEGRAM")

    model = maritalk.MariTalk(
        key=CHAVE_MARITACA,
        model="sabia-3"
    )

    bot = telebot.TeleBot(CHAVE_TELEGRAM)


    infracoes = {}

    @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
    def resposta(message):
        chat = get_chat(message.chat.id)

        if chat is None:
            chat = Group(message.chat.id)
            groups.append(chat)

        answer = model.generate(
            chat.prompt + " " + message.text + "\nResposta: ",
            chat_mode=False,
            do_sample=False,
            stopping_tokens=["\n"]
          )["answer"]
        chat_id = message.chat.id
        user_id = message.from_user.id

        print(" -- " + message.text + " -- ")
        print(answer)
        
        if "Sim" in answer:
            admins = bot.get_chat_administrators(message.chat.id)
            for admin in admins:
                if admin.user.id != bot.get_me().id: 
                    bot.send_message(admin.user.id, 
                                     f"O usuário {message.from_user.first_name} enviou uma mensagem nociva no grupo {message.chat.title}.\n\n"
                                     f"Mensagem: {message.text}")
            
            if (user_id, chat_id) in infracoes:
                infracoes[(user_id, chat_id)] += 1
            else:
                infracoes[(user_id, chat_id)] = 1

            bot.send_message(message.chat.id, f"O usuário {message.from_user.first_name} enviou uma mensagem nociva. {3 - infracoes[(user_id, chat_id)]} infrações restantes para remoção.")
            if infracoes[(user_id, chat_id)] >= 3:
                bot.send_message(chat_id, f"O usuário {message.from_user.first_name} foi removido do grupo por toxicidade.")
                infracoes[(user_id, chat_id)] = 0
                bot.kick_chat_member(chat_id, user_id)
            
            bot.delete_message(chat_id, message.message_id)


    bot.infinity_polling()