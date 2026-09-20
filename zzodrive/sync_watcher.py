"""Auto-sync: listen for new channel messages and add them to the index.

Since bots can't read channel history, we use real-time event listeners
instead of polling.
"""
import asyncio
import time

from telethon import events

from . import config, index, client_manager


_event_handler = None


def _extract_file_info(msg):
    """Extract file metadata from a Telethon message."""
    if not msg or not msg.document:
        return None

    name = None
    for attr in msg.document.attributes:
        if hasattr(attr, "file_name") and attr.file_name:
            name = attr.file_name
            break
    if not name:
        name = f"file_{msg.id}"

    remote_path = name
    if msg.message and msg.message.startswith("zzodrive:"):
        remote_path = msg.message[len("zzodrive:"):].strip()

    return {
        "msg_id": msg.id,
        "name": name,
        "size": msg.document.size,
        "remote_path": remote_path,
        "md5": None,
        "encrypted": False,
        "uploaded_at": int(msg.date.timestamp()) if msg.date else int(time.time()),
    }


def _register_listener():
    """Register an event handler on the shared client."""
    global _event_handler
    if _event_handler is not None:
        print("[sync] Listener already registered")
        return

    channel_id = int(config.get("ZZODRIVE_CHANNEL_ID"))

    async def _on_new_message(event):
        try:
            msg = event.message
            if msg is None or not msg.document:
                return

            info = _extract_file_info(msg)
            if not info:
                return

            # Skip if already in index
            if index.find(info["msg_id"]):
                return

            index.add(
                msg_id=info["msg_id"],
                name=info["name"],
                size=info["size"],
                remote_path=info["remote_path"],
                md5=info["md5"],
                encrypted=info["encrypted"],
            )
            print(f"[sync] ✅ Added new file: {info['name']} ({info['size']} bytes, id={info['msg_id']})")
        except Exception as e:
            print(f"[sync] handler error: {e}")

    client_manager._ensure_loop()

    async def _setup():
        client = await client_manager._get_client()
        client.add_event_handler(
            _on_new_message,
            events.NewMessage(chats=[channel_id]),
        )
        print(f"[sync] Listening for new files in channel {channel_id}")
        return True

    try:
        result = client_manager.run(_setup())
        _event_handler = _on_new_message
        print("[sync] Event listener registered")
    except Exception as e:
        print(f"[sync] Failed to register listener: {e}")


def start():
    """Start the event-based sync."""
    _register_listener()


def stop():
    """Remove event listener."""
    global _event_handler
    if _event_handler is None:
        return
    try:
        async def _teardown():
            client = await client_manager._get_client()
            client.remove_event_handler(_event_handler)
        client_manager.run(_teardown())
        _event_handler = None
        print("[sync] Listener removed")
    except Exception as e:
        print(f"[sync] teardown error: {e}")


def sync_now():
    """No-op in event mode (files arrive automatically)."""
    print("[sync] Event mode is active. New files are auto-added.")
    return 0
