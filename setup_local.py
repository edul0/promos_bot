"""Login local gratuito: credenciais digitadas pelo usuário, fora do chat."""
import asyncio
import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk


def main():
    root = tk.Tk()
    root.title('Noirl Promo — conectar Telegram neste computador')
    root.geometry('620x520')
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Conectar sua conta do Telegram', font=('Segoe UI', 18)).pack(anchor='w')
    ttk.Label(frame, text='Gratuito. Esta etapa faz o login; o monitor ainda não será iniciado.', wraplength=560).pack(anchor='w', pady=(8, 16))
    values = {}
    for label, name, secret in [('App api_id', 'api_id', False), ('App api_hash', 'api_hash', True), ('Telefone com DDI (ex.: +55...)', 'phone', False)]:
        ttk.Label(frame, text=label).pack(anchor='w', pady=(6, 2))
        entry = ttk.Entry(frame, show='*' if secret else '')
        entry.pack(fill='x')
        values[name] = entry
    status = tk.StringVar(value='Copie api_id e api_hash da página my.telegram.org/apps. Não envie esses dados no chat.')
    ttk.Label(frame, textvariable=status, wraplength=560).pack(anchor='w', pady=16)
    events = queue.Queue()
    replies = queue.Queue()
    private_dir = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'NoirlPromo'
    private_dir.mkdir(parents=True, exist_ok=True)
    try:
        saved = json.loads((private_dir / 'account.json').read_text(encoding='utf-8'))
        values['api_id'].insert(0, str(saved['api_id']))
        values['api_hash'].insert(0, saved['api_hash'])
    except (FileNotFoundError, ValueError, KeyError):
        pass

    async def authenticate(api_id, api_hash, phone):
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        from telethon.utils import get_peer_id
        client = TelegramClient(str(private_dir / 'telegram_user'), api_id, api_hash)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                events.put(('prompt', 'Digite o código recebido no seu Telegram:', False))
                code = await asyncio.to_thread(replies.get)
                try:
                    await client.sign_in(phone=phone, code=code)
                except SessionPasswordNeededError:
                    events.put(('prompt', 'Digite sua senha de verificação em duas etapas:', True))
                    password = await asyncio.to_thread(replies.get)
                    await client.sign_in(password=password)
            (private_dir / 'account.json').write_text(json.dumps({'api_id': api_id, 'api_hash': api_hash}), encoding='utf-8')
            config = json.loads(Path(__file__).with_name('watchlist.json').read_text(encoding='utf-8'))
            joined = {dialog.id async for dialog in client.iter_dialogs()}
            missing = []
            for name in config.get('chat_usernames', []):
                try:
                    entity = await client.get_entity(name)
                    if get_peer_id(entity) not in joined:
                        missing.append('@' + name)
                except Exception:
                    missing.append('@' + name)
            message = 'Conta conectada. Sessão salva apenas neste computador. O monitor ainda não está iniciado.'
            if missing:
                message += '\nEntre nestas fontes no Telegram para acompanhar novas mensagens: ' + ', '.join(missing)
            events.put(('done', message))
        except Exception as exc:
            # Não registra telefone, código, senha ou api_hash.
            events.put(('error', 'Não foi possível concluir o login (' + type(exc).__name__ + '). Confira os dados e tente novamente.'))
        finally:
            await client.disconnect()

    def connect():
        try:
            api_id = int(values['api_id'].get().strip())
            api_hash = values['api_hash'].get().strip()
            phone = values['phone'].get().strip()
            if len(api_hash) != 32 or not phone.startswith('+'):
                raise ValueError()
        except ValueError:
            status.set('Preencha api_id, api_hash de 32 caracteres e telefone com DDI.')
            return
        button.config(state='disabled')
        status.set('Conectando ao Telegram…')
        threading.Thread(target=lambda: asyncio.run(authenticate(api_id, api_hash, phone)), daemon=True).start()

    button = ttk.Button(frame, text='Conectar e salvar neste computador', command=connect)
    button.pack(anchor='w')

    def poll():
        try:
            while True:
                event = events.get_nowait()
                if event[0] == 'prompt':
                    dialog = tk.Toplevel(root)
                    dialog.title('Autenticação — Telegram')
                    dialog.transient(root)
                    dialog.grab_set()
                    ttk.Label(dialog, text=event[1], padding=16).pack()
                    answer = ttk.Entry(dialog, show='*' if event[2] else '')
                    answer.pack(fill='x', padx=16, pady=8)
                    def submit():
                        replies.put(answer.get().strip())
                        dialog.destroy()
                    ttk.Button(dialog, text='Confirmar no Telegram', command=submit).pack(pady=16)
                    dialog.protocol('WM_DELETE_WINDOW', lambda: (replies.put(''), dialog.destroy()))
                    answer.bind('<Return>', lambda _event: submit())
                    answer.focus_set()
                else:
                    status.set(event[1])
                    button.config(state='normal')
        except queue.Empty:
            pass
        root.after(150, poll)

    root.after(150, poll)
    root.mainloop()


if __name__ == '__main__':
    main()
