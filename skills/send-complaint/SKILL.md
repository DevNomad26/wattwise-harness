---
name: send-complaint
description: Email the complaint letter to the electricity authority with the send_complaint_email tool. Use when the user asks to send, email or submit the complaint letter. Nothing is sent unless that tool returns SENT.
---
# Send complaint

This skill is now loaded. It is instructions, not a tool: never call `send-complaint` or `load_skill` for it again. To send, call the `send_complaint_email` tool.

Follow these steps in order. The email address of the authority is fixed inside the tool; never ask for it or write one.

1. Find the letter. Use the complaint letter already in this conversation. If there is none, follow the `complaint-letter` skill, give the letter as the final answer, and ask the user to confirm that it should be sent. Do not send it in that reply.

2. Check what the user has given. You need the user's name, consumer number, and email login. The email login is hidden from you: when the user gives it, you see `[email login received]` instead. If any of the three is missing in this conversation, your next reply must be the final answer asking for what is missing. Ask for the email login in exactly this form, with a Gmail app password: `smtps://you@gmail.com:APP-PASSWORD@smtp.gmail.com`. Never ask for a password in any other form, and never invent a name or consumer number.

3. Prepare the letter. Replace `[Your Name]` and `[Consumer Number]` with what the user gave, and any `[Address]` or `[Phone]` the user gave. Leave every other line as it is: the tool fills in the date and removes address, phone and office lines the user did not give. The letter is only the letter, from "To," to the signature; leave out notes to the user such as "Please attach a copy of your bill."

4. Send it. Use the letter's subject line (without "Subject:") as the subject, and the bill photo path from this conversation as image_path:
   `{"action": "tool", "tool_name": "send_complaint_email", "tool_args": {"subject": "<subject line>", "letter": "<full letter from step 3>", "image_path": "<bill photo path>"}}`
   Leave out image_path if no bill photo path is in this conversation.

5. Read the result.
   - It says "NOT SENT" and asks for the name, consumer number or email login: ask the user for them in the final answer, as in step 2.
   - It says "NOT SENT" and names other placeholders: remove those lines and call `send_complaint_email` once more. Do not give the letter as the final answer instead.
   - It says "NOT SENT" for any other reason: the final answer says the letter was not sent, gives the reason in simple words, and gives the letter so the user can send it themselves. Do not call the tool again.
   - It says "SENT:": the final answer tells the user the letter was emailed, to which address, whether the bill photo was attached, and any sentences the tool left out.

Rules:
- Never say the letter was sent unless the tool result says "SENT:".
- Send each letter once. Do not call `send_complaint_email` again after it says "SENT:".
- Never invent a name, consumer number, address or phone number.
- Never repeat or write out an email login or password.
