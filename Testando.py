import maritalk
import telebot
from dotenv import load_dotenv
import os


prompt = """Você é um bot que decide se uma mensagem \
é nociva ou não, se possui preconceitos ou age com \
mal caráter em um grupo.

Reponda "Sim" se você detectar algo nocivo, \
preconceituoso ou mal intencionado na mensagem, \
ou "Não" caso contrário. 
E não diga absolutamente nada além disso, NADA ALÉM DISSO.
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


    @bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
    def resposta(message):
        chat = get_chat(message.chat.id)

        if chat is None:
            chat = Group(message.chat.id)
            groups.append(chat)

        answer = model.generate(
            chat.prompt,
            chat_mode=False,
            do_sample=False,
            stopping_tokens=["\n"]
        )["answer"]

        if "Sim" in answer:
            bot.reply_to(message, "Mensagem detectada como nociva.\n" + answer)
        else:
            bot.reply_to(message, "Mensagem não detectada como nociva.\n" + answer)


    bot.infinity_polling()
