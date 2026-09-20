"""Telegram bot commands for remote control."""
import asyncio

from telethon import events

from . import config, index, sync_watcher


def _human_size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def register(client):
    """Register bot command handlers on the client."""

    @client.on(events.NewMessage(pattern=r"^/start$"))
    async def _start(event):
        await event.reply(
            "🚀 **zzoDrive Bot**\n\n"
            "**Commands:**\n"
            "`/stats` — Show statistics\n"
            "`/list` — List 15 latest files\n"
            "`/search <query>` — Search files\n"
            "`/get <msg_id>` — Fetch a file\n"
            "`/sync` — Force sync from Telegram\n"
            "`/help` — Show this message"
        )

    @client.on(events.NewMessage(pattern=r"^/help$"))
    async def _help(event):
        await _start(event)

    @client.on(events.NewMessage(pattern=r"^/stats$"))
    async def _stats(event):
        s = index.stats()
        # count chunked files
        files = index.all_files()
        chunked = sum(1 for f in files if f.get("chunks"))
        await event.reply(
            f"📊 **zzoDrive Stats**\n\n"
            f"📁 Files: **{s['count']}**\n"
            f"💾 Size: **{_human_size(s['total_size'])}**\n"
            f"🔐 Encrypted: **{s['encrypted']}**\n"
            f"📦 Chunked: **{chunked}**"
        )

    @client.on(events.NewMessage(pattern=r"^/list(?:\s+(\d+))?$"))
    async def _list(event):
        n = int(event.pattern_match.group(1) or 15)
        n = min(n, 50)
        files = sorted(index.all_files(), key=lambda x: x.get("uploaded_at", 0), reverse=True)[:n]
        if not files:
            await event.reply("📂 No files yet.")
            return
        lines = [f"📂 **Latest {len(files)} file(s):**\n"]
        for f in files:
            enc = "🔐" if f.get("encrypted") else "📄"
            path = f.get("remote_path", f["name"])
            lines.append(f"`{f['msg_id']}` {enc} {path} — {_human_size(f['size'])}")
        await event.reply("\n".join(lines))

    @client.on(events.NewMessage(pattern=r"^/search\s+(.+)$"))
    async def _search(event):
        q = event.pattern_match.group(1).strip()
        if not q:
            await event.reply("Usage: `/search <query>`")
            return
        files = index.search(q)
        if not files:
            await event.reply(f"🔍 No matches for `{q}`")
            return
        lines = [f"🔍 **{len(files)} match(es) for** `{q}`:\n"]
        for f in files[:25]:
            enc = "🔐" if f.get("encrypted") else "📄"
            path = f.get("remote_path", f["name"])
            lines.append(f"`{f['msg_id']}` {enc} {path} — {_human_size(f['size'])}")
        if len(files) > 25:
            lines.append(f"\n_... and {len(files) - 25} more_")
        await event.reply("\n".join(lines))

    @client.on(events.NewMessage(pattern=r"^/get\s+(\d+)$"))
    async def _get(event):
        msg_id = int(event.pattern_match.group(1))
        entry = index.find(msg_id)
        if not entry:
            await event.reply(f"❌ No file with ID `{msg_id}`")
            return

        # Chunked file → send all chunks? For now, only single-file
        if entry.get("chunks"):
            await event.reply(
                f"📦 **{entry['name']}** is chunked ({len(entry['chunks'])} parts).\n"
                f"Download it from the web dashboard to reassemble."
            )
            return

        await event.reply(f"📤 Sending **{entry['name']}**...")
        try:
            channel_id = int(config.get("ZZODRIVE_CHANNEL_ID"))
            msg = await event.client.get_messages(channel_id, ids=msg_id)
            if not msg or not msg.document:
                await event.reply("❌ File not found in channel.")
                return
            await event.client.send_file(event.chat_id, msg.document, caption=entry["name"])
        except Exception as e:
            await event.reply(f"❌ Error: {e}")

    @client.on(events.NewMessage(pattern=r"^/sync$"))
    async def _sync(event):
        await event.reply("🔄 Syncing...")
        added = await asyncio.get_event_loop().run_in_executor(None, sync_watcher.sync_now)
        await event.reply(f"✅ Sync complete. Added **{added}** new file(s).")

    print("[bot] Command handlers registered")
