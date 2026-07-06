"""Gradio entrypoint: a chat pane plus an "under the hood" debug panel.

Run with: uv run python -m evbot.app

The debug panel is not cosmetic — being able to see the guardrail verdicts,
router decision, candidate answer(s), and judge scores for every turn is the
whole point of the lab. Uses gr.Blocks (not ChatInterface) so that second
panel has somewhere to live.
"""

import gradio as gr

from evbot.agent import answer_question

DEFAULT_SESSION_ID = "demo"


def handle_submit(message: str, chat_history: list[dict], session_id: str):
    if not message.strip():
        return "", chat_history, {}

    answer, debug = answer_question(message, session_id or DEFAULT_SESSION_ID)

    chat_history = chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return "", chat_history, debug


with gr.Blocks(title="EVBot — Week 3 Lab") as demo:
    gr.Markdown("# EVBot 🔋\nAsk me about EV models, charging, batteries, or incentives.")

    session_id_box = gr.Textbox(
        label="Session ID",
        value=DEFAULT_SESSION_ID,
        info="Keep this the same across restarts to test that conversation memory persists.",
    )

    with gr.Row():
        with gr.Column(scale=1):
            chatbot = gr.Chatbot(height=500)
            message_box = gr.Textbox(label="Your question", placeholder="e.g. What's the range of the Model 3?")
            submit_button = gr.Button("Send", variant="primary")

        with gr.Column(scale=1):
            gr.Markdown("### Under the hood")
            debug_panel = gr.JSON(label="Pipeline trace for the last turn")

    submit_button.click(
        handle_submit,
        inputs=[message_box, chatbot, session_id_box],
        outputs=[message_box, chatbot, debug_panel],
    )
    message_box.submit(
        handle_submit,
        inputs=[message_box, chatbot, session_id_box],
        outputs=[message_box, chatbot, debug_panel],
    )


if __name__ == "__main__":
    demo.launch()
