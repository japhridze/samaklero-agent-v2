import anthropic
import os
from sheets import get_properties, get_faq

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """შენ ხარ სამაკლერო კომპანიის ასისტენტი.
მეგობრულად, მოკლედ და ბუნებრივად — როგორც ნამდვილი ადამიანი.
არასოდეს დაწერო "მე ვარ AI" ან "ვარ ბოტი".
თუ კითხვა ობიექტებზეა — მიეცი კონკრეტული ინფო.
თუ ვერ პოულობ შესაფერ ობიექტს — სთხოვე დაზუსტება.
პასუხი მოკლე იყოს — მაქსიმუმ 3-4 წინადადება.
დაამთავრე პასუხი კითხვით ან call-to-action-ით.
თუ მომხმარებელი ფოტოს ითხოვს — გაუგზავნე ფოტო_ლინკი პირდაპირ."""

def generate_reply(user_message: str, conversation_history: list = [], sheet_id: str = "") -> str:
    properties = get_properties(sheet_id, user_message)
    faq = get_faq(sheet_id)

    context = f"""ხელმისაწვდომი ობიექტები:
{properties}

ხშირი კითხვები და პასუხები:
{faq}"""

    messages = conversation_history + [
        {"role": "user", "content": user_message}
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        system=SYSTEM_PROMPT + f"\n\nმონაცემთა ბაზა:\n{context}",
        messages=messages
    )

    return response.content[0].text