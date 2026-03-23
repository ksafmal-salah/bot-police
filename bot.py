"""
بوت نيولوس — إدارة الأمن العام v1
✅ رتب عسكرية كاملة
✅ تحديث رتبة Discord تلقائياً عند الترقية
✅ DM ترقية مخصص بالرتب العسكرية
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp, asyncio, json, os, urllib.parse
from datetime import datetime, timedelta

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
API_URL        = "https://script.google.com/macros/s/AKfycbwR3ROHGwpdRdLa0_gnDdksNESbbUI9cPeMneMR26inCxv1zFwwH9n212nZZZx2td-i/exec"
ATTENDANCE_API = os.getenv("ATT_URL", "https://script.google.com/macros/s/AKfycbxnbYiMJ9UFsBkgJge20UrOuEW0-Z85791mECFV1ku_f5sKmOWHNn2wsVD-cDq2evKZkw/exec")
BOT_TOKEN      = os.getenv("BOT_TOKEN", "")

def _int(k, d="0"):
    try: return int(os.getenv(k, d))
    except: return 0

GUILD_ID           = _int("GUILD_ID",          "1483226560973770885")
ROLE_CAN_PROMOTE   = _int("ROLE_CAN_PROMOTE",  "1482934455671721994")
ROLE_CAN_VIOLATE   = _int("ROLE_CAN_VIOLATE",  "0")
CHANNEL_REPORTS    = _int("CHANNEL_REPORTS",   "1482934174062084260")
CHANNEL_PROMOS     = _int("CHANNEL_PROMOS",    "1482934174062084260")
CHANNEL_VIOLATIONS = _int("CHANNEL_VIOLATIONS","1482934174062084260")
CHANNEL_HOURS_DONE = _int("CHANNEL_HOURS_DONE","1482934174062084260")

ROLE_IDS = {
    "جندي":                         _int("ROLE_JUNDI"),
    "جندي أول":                     _int("ROLE_JUNDI_AWAL"),
    "عريف":                         _int("ROLE_ARIF"),
    "وكيل رقيب":                    _int("ROLE_WAKIL"),
    "رقيب":                         _int("ROLE_RAQIB"),
    "رقيب أول":                     _int("ROLE_RAQIB_AWAL"),
    "رئيس رقباء":                   _int("ROLE_RAEES"),
    "ملازم":                        _int("ROLE_MULAZIM"),
    "ملازم أول":                    _int("ROLE_MULAZIM_AWAL"),
    "نقيب":                         _int("ROLE_NAQIB"),
    "رائد":                         _int("ROLE_RAED"),
    "مقدم ركن":                     _int("ROLE_MUQADDAM"),
    "عقيد ركن":                     _int("ROLE_AQID"),
    "عميد ركن":                     _int("ROLE_AMID"),
    "لواء ركن":                     _int("ROLE_LIWA"),
    "فريق ركن":                     _int("ROLE_FAREEQ"),
    "فريق أول ركن":                 _int("ROLE_FAREEQ_AWAL"),
    "مساعد قائد الأمن العام":       _int("ROLE_ASSIST"),
    "نائب مساعد قائد الأمن العام":  _int("ROLE_VASSIST"),
    "نائب قائد الأمن العام":        _int("ROLE_VICE"),
    "قائد الأمن العام":             _int("ROLE_LEAD"),
}

def _parse_ids(key: str) -> set:
    raw = os.getenv(key, "")
    ids = set()
    for x in raw.split(","):
        x = x.strip()
        if x.isdigit():
            ids.add(int(x))
    return ids

SUPER_ADMIN_IDS: set = _parse_ids("SUPER_ADMINS")
SUPER_ADMIN_IDS.add(564573948126429194)  # صالح العنزي

PROMOTE_MAP = {
    "جندي":        "جندي أول",
    "جندي أول":    "عريف",
    "عريف":        "وكيل رقيب",
    "وكيل رقيب":  "رقيب",
    "رقيب":        "رقيب أول",
    "رقيب أول":    "رئيس رقباء",
    "رئيس رقباء": "ملازم",
    "ملازم":       "ملازم أول",
    "ملازم أول":   "نقيب",
    "نقيب":        "رائد",
    "رائد":        "مقدم ركن",
    "مقدم ركن":    "عقيد ركن",
}

PROMO_HOURS = {
    "جندي":6, "جندي أول":10, "عريف":14, "وكيل رقيب":18,
    "رقيب":22, "رقيب أول":26, "رئيس رقباء":30,
    "ملازم":35, "ملازم أول":40, "نقيب":45, "رائد":50,
}

ADMIN_ONLY_LEVELS = [
    "مقدم ركن","عقيد ركن","عميد ركن","لواء ركن","فريق ركن","فريق أول ركن",
    "مساعد قائد الأمن العام","نائب مساعد قائد الأمن العام",
    "نائب قائد الأمن العام","قائد الأمن العام",
]

REQUIRED_COURSES = {
    "جندي أول":   ["c1"],
    "عريف":        ["c1"],
    "وكيل رقيب":  ["c1","c2"],
    "رقيب":        ["c1","c2"],
    "رقيب أول":   ["c1","c2","c3"],
    "رئيس رقباء": ["c1","c2","c3"],
    "ملازم":       ["c1","c2","c3","c4"],
    "ملازم أول":  ["c1","c2","c3","c4"],
    "نقيب":        ["c1","c2","c3","c4"],
    "رائد":        ["c1","c2","c3","c4","c5"],
}

LEVEL_RANGES = {
    "جندي":                         (450,499),
    "جندي أول":                     (400,449),
    "عريف":                         (350,399),
    "وكيل رقيب":                    (300,349),
    "رقيب":                         (250,299),
    "رقيب أول":                     (200,249),
    "رئيس رقباء":                   (150,199),
    "ملازم":                        (110,149),
    "ملازم أول":                    (80,109),
    "نقيب":                         (60,79),
    "رائد":                         (37,59),
    "مقدم ركن":                     (20,36),
    "عقيد ركن":                     (11,19),
    "عميد ركن":                     (5,10),
    "لواء ركن":                     (3,4),
    "فريق ركن":                     (2,2),
    "فريق أول ركن":                 (1,1),
    "مساعد قائد الأمن العام":       (3,4),
    "نائب مساعد قائد الأمن العام":  (5,10),
    "نائب قائد الأمن العام":        (2,2),
    "قائد الأمن العام":             (1,1),
}

COURSE_NAMES = {
    "c1":"دورة العمليات","c2":"دورة التصنيع",
    "c3":"دورة التعديل والتزويد","c4":"دورة الإشراف","c5":"دورة شؤون التوظيف",
}

PERM_LABELS = {
    "all":     "كل الصلاحيات",
    "promote": "ترقية / استقالة / فصل",
    "violate": "تسجيل مخالفات",
    "courses": "منح دورات فقط",
}

C_GOLD=0xE8B84B; C_GREEN=0x2ECC8A; C_RED=0xE85555
C_BLUE=0x4A90E8; C_AMBER=0xE8A82E; C_PURPLE=0x9B6FE8

# ══════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

notified_hours: set = set()
BOT_PERMISSIONS: dict = {}

async def load_permissions():
    global BOT_PERMISSIONS
    try:
        res = await api_get("getPermissions")
        if res.get("status") == "ok" and res.get("data"):
            BOT_PERMISSIONS = {int(k): v for k, v in res["data"].items()}
            print(f"✅ تم تحميل صلاحيات {len(BOT_PERMISSIONS)} عضو")
    except Exception as e:
        print(f"[PERMS LOAD ERR] {e}")

async def save_permissions():
    try:
        data = {str(k): v for k, v in BOT_PERMISSIONS.items()}
        await api_post("saveConfig", {"key": "botPermissions", "value": data})
    except Exception as e:
        print(f"[PERMS SAVE ERR] {e}")

def guild_obj(): return discord.Object(id=GUILD_ID)

# ══════════════════════════════════════════
#  PERMISSION SYSTEM
# ══════════════════════════════════════════
def is_super_admin(m: discord.Member) -> bool:
    if m.guild_permissions.administrator: return True
    return m.id in SUPER_ADMIN_IDS

def has_perm(m: discord.Member, perm: str) -> bool:
    if is_super_admin(m): return True
    p = BOT_PERMISSIONS.get(m.id, {})
    return p.get("all", False) or p.get(perm, False)

def can_promote(m: discord.Member) -> bool:
    if is_super_admin(m): return True
    if ROLE_CAN_PROMOTE and any(r.id == ROLE_CAN_PROMOTE for r in m.roles): return True
    return has_perm(m, "promote")

def can_violate(m: discord.Member) -> bool:
    if is_super_admin(m): return True
    if ROLE_CAN_VIOLATE and any(r.id == ROLE_CAN_VIOLATE for r in m.roles): return True
    return has_perm(m, "violate") or has_perm(m, "promote")

def can_courses(m: discord.Member) -> bool:
    if is_super_admin(m): return True
    return has_perm(m, "courses") or has_perm(m, "promote")

def can_view_admin(m: discord.Member) -> bool:
    return can_promote(m) or can_violate(m) or can_courses(m)

# ══════════════════════════════════════════
#  API HELPERS
# ══════════════════════════════════════════
async def api_get(action: str) -> dict:
    url = f"{API_URL}?action={urllib.parse.quote(action)}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.json(content_type=None)
    except Exception as e:
        print(f"[GET ERR] {action}: {e}")
        return {}

async def api_post(action: str, payload: dict = {}) -> dict:
    body = {"action": action, **payload}
    url = f"{API_URL}?action={urllib.parse.quote(action)}&payload={urllib.parse.quote(json.dumps(body, ensure_ascii=False))}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.json(content_type=None)
    except Exception as e:
        print(f"[POST ERR] {action}: {e}")
        return {}

# ══════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════
def fmt_hours(h: float) -> str:
    hrs=int(h); mins=int((h-hrs)*60)
    return f"{hrs}:{str(mins).zfill(2)}"

def pbar(cur: float, total: float, n: int=10) -> str:
    if total<=0: return "░"*n
    f=int(min(1.0,cur/total)*n)
    return "█"*f+"░"*(n-f)

def now_str() -> str: return datetime.now().strftime("%Y-%m-%d %H:%M")

def err_embed(msg: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {msg}", color=C_RED)

def foot(e: discord.Embed) -> discord.Embed:
    e.set_footer(text=f"نظام نيولوس — إدارة الأمن العام • {now_str()}")
    return e

def parse_courses(data: list, gid: str) -> set:
    done = set()
    for l in data:
        if isinstance(l, dict):
            if str(l.get("gid","")).upper() == gid:
                cid = l.get("courseId","")
                if cid: done.add(cid)
        elif isinstance(l, (list,tuple)) and len(l) > 3:
            if str(l[1]).upper() == gid:
                cid = str(l[3])
                if cid: done.add(cid)
    return done

async def get_member(gid: str):
    gid = gid.upper().strip()
    d = await api_get("getMembers")
    return next((m for m in d.get("data",[]) if str(m[0]).upper()==gid), None)

async def get_member_by_discord(did: str):
    d = await api_get("getMembers")
    return next((m for m in d.get("data",[])
                 if str(m[4]).strip()==str(did) and m[7]!="منصب شاغر"), None)

async def get_first_vacant(level: str):
    r_s, r_e = LEVEL_RANGES.get(level,(0,0))
    d = await api_get("getMembers")
    live = {str(m[0]).upper() for m in d.get("data",[]) if m[7]!="منصب شاغر"}
    for n in range(r_s, r_e+1):
        gid = f"G-{str(n).zfill(3)}"
        if gid not in live: return gid
    return None

async def update_role(discord_id: str, old_lvl: str, new_lvl: str):
    if not discord_id or str(discord_id).strip() in ("—", "", "None"):
        print(f"[ROLE SKIP] لا يوجد Discord ID")
        return
    try:
        g = bot.get_guild(GUILD_ID)
        if not g: return
        mem = await g.fetch_member(int(discord_id))
        old_role_id = ROLE_IDS.get(old_lvl, 0)
        new_role_id = ROLE_IDS.get(new_lvl, 0)
        if old_role_id:
            old_r = g.get_role(old_role_id)
            if old_r and old_r in mem.roles:
                await mem.remove_roles(old_r, reason=f"ترقية من {old_lvl} إلى {new_lvl}")
        if new_role_id:
            new_r = g.get_role(new_role_id)
            if new_r:
                await mem.add_roles(new_r, reason=f"ترقية من {old_lvl} إلى {new_lvl}")
    except discord.NotFound:
        print(f"[ROLE ERR] العضو {discord_id} غير موجود في السيرفر")
    except discord.Forbidden:
        print(f"[ROLE ERR] البوت ما عنده صلاحية تعديل الرتب")
    except Exception as e:
        print(f"[ROLE ERR] {e}")

async def update_nickname(discord_id: str, new_gid: str, name: str) -> bool:
    if not discord_id or str(discord_id).strip() in ("—", "", "None"):
        return False
    try:
        g = bot.get_guild(GUILD_ID)
        if not g: return False
        mem = await g.fetch_member(int(discord_id))
        new_nick = f"[{new_gid}] {name}"
        if len(new_nick) > 32:
            new_nick = new_nick[:32]
        await mem.edit(nick=new_nick, reason=f"تحديث GID إلى {new_gid}")
        print(f"[NICK] ✅ {mem.name} → {new_nick}")
        return True
    except discord.Forbidden:
        print(f"[NICK FORBIDDEN] {discord_id}")
        return False
    except Exception as e:
        print(f"[NICK ERR] {e}")
        return False

async def calc_hours(gid: str) -> float:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(ATTENDANCE_API, timeout=aiohttp.ClientTimeout(total=15)) as r:
                rows = await r.json(content_type=None)
        if not isinstance(rows,list) or len(rows)<2: return 0.0
        data = [r for r in rows[1:] if str(r[0]).strip()==gid]
        ms=0; adj=0.0; li=None
        for row in data:
            act = str(row[3] if len(row)>3 else "").strip()
            ts  = str(row[4] if len(row)>4 else "")
            if act in ("ADJUST","ADJUST_HOURS"):
                try: adj += float(row[5] if len(row)>5 else 0)
                except: pass
                continue
            try: dt = datetime.fromisoformat(ts)
            except: dt = None
            if act=="دخول": li=dt
            elif act=="خروج" and li and dt and dt>li:
                ms += (dt-li).total_seconds()*1000; li=None
        return max(0.0, ms/3600000+adj)
    except: return 0.0

# ══════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅ {bot.user} | Guild: {GUILD_ID}")
    print(f"⭐ Super Admins: {SUPER_ADMIN_IDS}")
    print(f"📋 السيرفرات: {[g.name for g in bot.guilds]}")
    try:
        # امسح الأوامر القديمة وأعد sync
        tree.clear_commands(guild=guild_obj())
        synced = await tree.sync(guild=guild_obj())
        print(f"✅ {len(synced)} أمر تم sync بنجاح")
        for cmd in synced:
            print(f"   /{cmd.name}")
    except discord.Forbidden as e:
        print(f"❌ Forbidden — تأكد البوت في السيرفر وعنده صلاحية applications.commands: {e}")
    except discord.HTTPException as e:
        print(f"❌ HTTP error أثناء sync: {e}")
    except Exception as e:
        print(f"❌ sync error: {e}")
    await load_permissions()
    if not daily_report.is_running():    daily_report.start()
    if not hours_check.is_running():     hours_check.start()
    if not weekly_reminder.is_running(): weekly_reminder.start()


@bot.command(name="sync")
async def force_sync(ctx):
    """أمر طوارئ لـ sync الأوامر يدوياً — !sync في الشات"""
    if ctx.author.id not in SUPER_ADMIN_IDS and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ ما عندك صلاحية")
    await ctx.send("⏳ جاري sync الأوامر...")
    try:
        tree.clear_commands(guild=discord.Object(id=ctx.guild.id))
        synced = await tree.sync(guild=discord.Object(id=ctx.guild.id))
        await ctx.send(f"✅ تم sync **{len(synced)}** أمر بنجاح!")
    except Exception as e:
        await ctx.send(f"❌ فشل sync: {e}")

# ══════════════════════════════════════════
#  أوامر العسكري الشخصية (متاحة للجميع)
# ══════════════════════════════════════════

@tree.command(name="ملفي", description="ملفك الشخصي — ساعات + دورات + مخالفات", guild=guild_obj())
async def cmd_my_profile(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    m = await get_member_by_discord(str(i.user.id))
    if not m:
        return await i.followup.send(embed=err_embed("لم يُربط حسابك بـ G-ID — تواصل مع الإدارة"), ephemeral=True)
    gid = str(m[0]).upper()
    vd  = await api_get("getViolations")
    viols = [v for v in vd.get("data",[]) if str(v[1]).upper()==gid]
    cd  = await api_get("getCourseLog")
    done = parse_courses(cd.get("data",[]), gid)
    hours = await calc_hours(gid)
    req = PROMO_HOURS.get(m[2])
    nxt = PROMOTE_MAP.get(m[2],"")
    req_next = set(REQUIRED_COURSES.get(nxt,[]))
    embed = discord.Embed(title=f"🪖 ملفي — {m[1]}", color=C_GOLD)
    embed.add_field(name="G-ID",        value=f"`{m[0]}`", inline=True)
    embed.add_field(name="الرتبة",      value=m[2] or "—", inline=True)
    embed.add_field(name="الحالة",      value=m[7] or "—", inline=True)
    embed.add_field(name="المسمى",      value=m[3] or "—", inline=True)
    embed.add_field(name="الانضمام",    value=m[5] or "—", inline=True)
    embed.add_field(name="⚠️ مخالفات", value=str(len(viols)), inline=True)
    hrs_txt = f"**{fmt_hours(hours)}**"
    if req:
        bar = pbar(hours, req)
        pct = min(100, int(hours/req*100))
        hrs_txt += f"\n`{bar}` **{pct}%** ({fmt_hours(hours)}/{req}س)"
        if hours >= req: hrs_txt += "\n✅ مؤهل من ناحية الساعات!"
    else:
        hrs_txt += "\nℹ️ لا يوجد شرط ساعات"
    embed.add_field(name="⏱️ الساعات", value=hrs_txt, inline=False)
    ct = ""
    for cid, cname in COURSE_NAMES.items():
        if cid in done:          ct += f"✅ **{cname}**\n"
        elif cid in req_next:    ct += f"🔴 **{cname}** *(مطلوبة للترقية)*\n"
        else:                    ct += f"⬜ {cname}\n"
    embed.add_field(name="📚 الدورات", value=ct or "—", inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="ساعاتي", description="ساعات حضورك وتقدمك", guild=guild_obj())
async def cmd_my_hours(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    m = await get_member_by_discord(str(i.user.id))
    if not m:
        return await i.followup.send(embed=err_embed("لم يُربط حسابك — تواصل مع الإدارة"), ephemeral=True)
    gid = str(m[0]).upper()
    hours = await calc_hours(gid)
    req = PROMO_HOURS.get(m[2])
    embed = discord.Embed(title=f"⏱️ ساعاتي — {m[1]}", color=C_BLUE)
    embed.add_field(name="G-ID",    value=f"`{gid}`",               inline=True)
    embed.add_field(name="الرتبة", value=m[2],                      inline=True)
    embed.add_field(name="الساعات",value=f"**{fmt_hours(hours)}**", inline=True)
    if req:
        bar = pbar(hours, req)
        pct = min(100, int(hours/req*100))
        embed.add_field(name=f"التقدم ({req}س مطلوبة)",
                        value=f"`{bar}` **{pct}%** ({fmt_hours(hours)}/{req})", inline=False)
        if hours >= req: embed.add_field(name="", value="✅ أكملت الساعات المطلوبة!", inline=False)
    else:
        embed.add_field(name="", value="ℹ️ لا يوجد شرط ساعات لرتبتك الحالية", inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="مخالفاتي", description="مخالفاتك المسجلة", guild=guild_obj())
async def cmd_my_viols(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    m = await get_member_by_discord(str(i.user.id))
    if not m:
        return await i.followup.send(embed=err_embed("لم يُربط حسابك"), ephemeral=True)
    gid = str(m[0]).upper()
    vd = await api_get("getViolations")
    viols = sorted([v for v in vd.get("data",[]) if str(v[1]).upper()==gid], key=lambda x:x[0], reverse=True)
    if not viols:
        return await i.followup.send(embed=discord.Embed(description="✅ لا توجد مخالفات مسجلة في ملفك", color=C_GREEN), ephemeral=True)
    embed = discord.Embed(title=f"⚠️ مخالفاتي — {m[1]}", color=C_RED)
    embed.add_field(name="الإجمالي", value=str(len(viols)), inline=True)
    embed.add_field(name="فصل",     value=str(sum(1 for v in viols if v[4]=="فصل")),   inline=True)
    embed.add_field(name="إنذار",   value=str(sum(1 for v in viols if v[4]=="إنذار")), inline=True)
    for v in viols[:5]:
        try: ds=datetime.fromtimestamp(int(v[0])/1000).strftime("%Y-%m-%d")
        except: ds="—"
        e="🔴" if v[4]=="فصل" else "🟡" if v[4]=="إنذار" else "🔵"
        extra = f"| {v[6]}" if len(v)>6 and v[6] and v[6]!="—" else ""
        embed.add_field(name=f"{e} {v[3]}", value=f"**{v[5]}** {extra} — {ds}", inline=False)
    if len(viols)>5: embed.set_footer(text=f"آخر 5 من {len(viols)} • نظام نيولوس")
    else: foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="دوراتي", description="دوراتك وتقدمك نحو الترقية", guild=guild_obj())
async def cmd_my_courses(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    m = await get_member_by_discord(str(i.user.id))
    if not m:
        return await i.followup.send(embed=err_embed("لم يُربط حسابك"), ephemeral=True)
    gid = str(m[0]).upper()
    cd = await api_get("getCourseLog")
    done = parse_courses(cd.get("data",[]), gid)
    nxt = PROMOTE_MAP.get(m[2],"")
    req = set(REQUIRED_COURSES.get(nxt,[]))
    embed = discord.Embed(title=f"📚 دوراتي — {m[1]}", color=C_BLUE)
    embed.add_field(name="الرتبة",        value=m[2],              inline=True)
    embed.add_field(name="أتممت",         value=f"{len(done)}/5",  inline=True)
    embed.add_field(name="الرتبة القادمة",value=nxt or "—",        inline=True)
    ct = ""
    for cid, cname in COURSE_NAMES.items():
        if cid in done:   ct += f"✅ **{cname}** — مكتملة\n"
        elif cid in req:  ct += f"🔴 **{cname}** — *مطلوبة للترقية*\n"
        else:             ct += f"⬜ {cname}\n"
    embed.add_field(name="الدورات", value=ct, inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


# ══════════════════════════════════════════
#  البحث والعرض (للجميع)
# ══════════════════════════════════════════

@tree.command(name="عسكري", description="عرض ملف عسكري كامل", guild=guild_obj())
@app_commands.describe(gid="كود العسكري — مثال: G-001")
async def cmd_member(i: discord.Interaction, gid: str):
    await i.response.defer()
    m = await get_member(gid)
    if not m: return await i.followup.send(embed=err_embed(f"العسكري **{gid.upper()}** غير موجود"))
    vd = await api_get("getViolations")
    viols = [v for v in vd.get("data",[]) if str(v[1]).upper()==gid.upper()]
    cd = await api_get("getCourseLog")
    done = parse_courses(cd.get("data",[]), gid.upper())
    embed = discord.Embed(title=f"🪖 {m[1]}", color=C_GOLD)
    embed.add_field(name="G-ID",       value=f"`{m[0]}`",                                   inline=True)
    embed.add_field(name="الرتبة",     value=m[2] or "—",                                   inline=True)
    embed.add_field(name="الحالة",     value=m[7] or "—",                                   inline=True)
    embed.add_field(name="المسمى",     value=m[3] or "—",                                   inline=True)
    embed.add_field(name="Discord",    value=f"<@{m[4]}>" if m[4] and m[4]!="—" else "—",  inline=True)
    embed.add_field(name="الانضمام",   value=m[5] or "—",                                   inline=True)
    embed.add_field(name="⚠️ مخالفات",value=str(len(viols)),                                inline=True)
    embed.add_field(name="📚 دورات",   value=f"{len(done)}/5",                              inline=True)
    if len(m)>8 and m[8] and m[8]!="—":
        embed.add_field(name="ملاحظات",value=m[8][:200],inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="بحث", description="بحث عن عسكري بالاسم أو Discord ID أو G-ID", guild=guild_obj())
@app_commands.describe(query="الاسم أو Discord ID أو G-ID")
async def cmd_search(i: discord.Interaction, query: str):
    await i.response.defer()
    d = await api_get("getMembers"); members = d.get("data",[])
    q = query.lower().strip().lstrip("<@>").rstrip(">")
    results = [m for m in members
               if m[7]!="منصب شاغر" and m[1] and m[1]!="—"
               and (q in str(m[1]).lower() or q in str(m[0]).lower() or q in str(m[4]).lower())][:8]
    if not results: return await i.followup.send(embed=err_embed("لا توجد نتائج"))
    embed = discord.Embed(title=f"🔍 نتائج البحث ({len(results)})", color=C_BLUE)
    for m in results:
        d2 = f"<@{m[4]}>" if m[4] and m[4]!="—" else "—"
        embed.add_field(name=f"`{m[0]}` — {m[1]}", value=f"{m[2]} • {m[7]} • {d2}", inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="حضور", description="ساعات حضور عسكري", guild=guild_obj())
@app_commands.describe(gid="كود العسكري")
async def cmd_att(i: discord.Interaction, gid: str):
    await i.response.defer()
    gid = gid.upper().strip()
    m = await get_member(gid)
    hours = await calc_hours(gid)
    name=m[1] if m else gid; level=m[2] if m else "—"
    req = PROMO_HOURS.get(level)
    embed = discord.Embed(title=f"⏱️ حضور {name}", color=C_BLUE)
    embed.add_field(name="G-ID",    value=f"`{gid}`",               inline=True)
    embed.add_field(name="الرتبة", value=level,                     inline=True)
    embed.add_field(name="الساعات",value=f"**{fmt_hours(hours)}**", inline=True)
    if req:
        bar=pbar(hours,req); pct=min(100,int(hours/req*100))
        embed.add_field(name=f"التقدم ({req}س مطلوبة)",
                        value=f"`{bar}` **{pct}%** ({fmt_hours(hours)}/{req})", inline=False)
        if hours>=req: embed.add_field(name="",value="✅ مؤهل!",inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="مخالفات_عسكري", description="سجل مخالفات عسكري", guild=guild_obj())
@app_commands.describe(gid="كود العسكري")
async def cmd_viols(i: discord.Interaction, gid: str):
    await i.response.defer()
    gid=gid.upper().strip()
    vd=await api_get("getViolations")
    viols=sorted([v for v in vd.get("data",[]) if str(v[1]).upper()==gid],key=lambda x:x[0],reverse=True)
    m=await get_member(gid); name=m[1] if m else gid
    if not viols:
        return await i.followup.send(embed=discord.Embed(description=f"✅ لا توجد مخالفات للعسكري **{name}**",color=C_GREEN))
    embed=discord.Embed(title=f"⚠️ مخالفات {name}",color=C_RED)
    embed.add_field(name="الإجمالي",value=str(len(viols)),inline=True)
    embed.add_field(name="فصل",     value=str(sum(1 for v in viols if v[4]=="فصل")),   inline=True)
    embed.add_field(name="إنذار",   value=str(sum(1 for v in viols if v[4]=="إنذار")), inline=True)
    for v in viols[:5]:
        try: ds=datetime.fromtimestamp(int(v[0])/1000).strftime("%Y-%m-%d")
        except: ds="—"
        e="🔴" if v[4]=="فصل" else "🟡" if v[4]=="إنذار" else "🔵"
        extra = f"| {v[6]}" if len(v)>6 and v[6] and v[6]!="—" else ""
        embed.add_field(name=f"{e} {v[3]}", value=f"**{v[5]}** {extra} — {ds}", inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="دورات_عسكري", description="دورات عسكري وتقدمه", guild=guild_obj())
@app_commands.describe(gid="كود العسكري")
async def cmd_courses(i: discord.Interaction, gid: str):
    await i.response.defer()
    gid=gid.upper().strip()
    m=await get_member(gid); name=m[1] if m else gid; level=m[2] if m else "—"
    cd=await api_get("getCourseLog"); done=parse_courses(cd.get("data",[]),gid)
    nxt=PROMOTE_MAP.get(level,""); req=set(REQUIRED_COURSES.get(nxt,[]))
    embed=discord.Embed(title=f"📚 دورات {name}",color=C_BLUE)
    embed.add_field(name="الرتبة",        value=level,           inline=True)
    embed.add_field(name="أتم",           value=f"{len(done)}/5",inline=True)
    embed.add_field(name="الرتبة القادمة",value=nxt or "—",      inline=True)
    ct=""
    for cid,cname in COURSE_NAMES.items():
        if cid in done:   ct+=f"✅ {cname}\n"
        elif cid in req:  ct+=f"🔴 {cname} *(مطلوبة للترقية)*\n"
        else:             ct+=f"⬜ {cname}\n"
    embed.add_field(name="الدورات",value=ct or "—",inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


# ══════════════════════════════════════════
#  أوامر الإدارة
# ══════════════════════════════════════════

@tree.command(name="ترقية", description="ترقية عسكري للرتبة التالية", guild=guild_obj())
@app_commands.describe(gid="كود العسكري", ملاحظة="سبب الترقية (اختياري)")
async def cmd_promote(i: discord.Interaction, gid: str, ملاحظة: str=""):
    await i.response.defer()
    if not can_promote(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية الترقية"), ephemeral=True)
    gid=gid.upper().strip()
    m=await get_member(gid)
    if not m: return await i.followup.send(embed=err_embed(f"العسكري **{gid}** غير موجود"))
    cur=m[2]; nxt=PROMOTE_MAP.get(cur)
    if not nxt:
        return await i.followup.send(embed=discord.Embed(
            description=f"⭐ رتبة **{cur}** تحتاج موافقة القيادة للترقية", color=C_AMBER))

    cd=await api_get("getCourseLog")
    done=parse_courses(cd.get("data",[]),gid)
    missing=[c for c in REQUIRED_COURSES.get(nxt,[]) if c not in done]
    if missing:
        ms_list = "\n".join(f"• {COURSE_NAMES.get(c,c)}" for c in missing)
        return await i.followup.send(embed=discord.Embed(
            title="❌ دورات ناقصة",
            description=f"يجب إتمام الدورات التالية أولاً:\n{ms_list}",
            color=C_RED))

    discord_id = str(m[4]).strip() if m[4] and str(m[4]).strip() not in ("—","","None") else ""

    new_gid = await get_first_vacant(nxt)
    if not new_gid:
        return await i.followup.send(embed=discord.Embed(
            description="⛔ جميع مناصب الرتبة التالية ممتلئة", color=C_RED))

    notes = (m[8] if len(m)>8 else "") or ""
    notes += f" | ترقية من {cur} ({gid}) بواسطة {i.user.name}"
    if ملاحظة: notes += f" — {ملاحظة}"

    await api_post("addMember", {
        "gid":new_gid,"name":m[1],"level":nxt,"role":nxt,
        "discordId":discord_id,"joinDate":m[5] or "",
        "email":"","status":"نشط","notes":notes
    })
    await api_post("deleteMember", {"gid":gid})

    nick_updated = False
    if discord_id:
        await update_role(discord_id, cur, nxt)
        nick_updated = await update_nickname(discord_id, new_gid, m[1])

    dm_sent = False
    if discord_id:
        dm_sent = await send_promotion_dm(
            discord_id=discord_id,
            name=m[1],
            old_gid=gid,
            new_gid=new_gid,
            old_level=cur,
            new_level=nxt,
            admin_name=i.user.display_name,
            note=ملاحظة
        )

    if discord_id:
        role_status = "✅ تم تحديثها"
        nick_status = f"✅ `[{new_gid}] {m[1]}`" if nick_updated else "⚠️ فشل (Owner أو لا صلاحية)"
        dm_status   = "✅ تم الإرسال" if dm_sent else "⚠️ أغلق DMs"
    else:
        role_status = nick_status = dm_status = "⚠️ لا يوجد Discord ID"

    embed=discord.Embed(title="✅ تمت الترقية", color=C_GREEN)
    embed.add_field(name="العسكري",    value=f"**{m[1]}**",              inline=False)
    embed.add_field(name="من",         value=f"`{gid}` — {cur}",         inline=True)
    embed.add_field(name="إلى",        value=f"`{new_gid}` — **{nxt}**", inline=True)
    embed.add_field(name="بواسطة",     value=i.user.mention,             inline=True)
    embed.add_field(name="🎭 الرتبة",  value=role_status,                inline=True)
    embed.add_field(name="📛 الاسم",   value=nick_status,                inline=True)
    embed.add_field(name="📨 DM",      value=dm_status,                  inline=True)
    if ملاحظة: embed.add_field(name="ملاحظة", value=ملاحظة, inline=False)
    foot(embed)
    await i.followup.send(embed=embed)
    if CHANNEL_PROMOS:
        ch=bot.get_channel(CHANNEL_PROMOS)
        if ch and ch!=i.channel: await ch.send(embed=embed)


@tree.command(name="مخالفة", description="تسجيل مخالفة لعسكري", guild=guild_obj())
@app_commands.describe(gid="كود العسكري",نوع="نوع المخالفة",عقوبة="العقوبة",
                       تصنيف="فصل / إنذار / خصم",غرامة="المبلغ",أيام="مدة الحظر")
async def cmd_violation(i: discord.Interaction, gid: str, نوع: str, عقوبة: str,
                        تصنيف: str="إنذار", غرامة: str="", أيام: str=""):
    await i.response.defer()
    if not can_violate(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية تسجيل المخالفات"), ephemeral=True)
    gid=gid.upper().strip()
    m=await get_member(gid); name=m[1] if m else gid
    await api_post("addViolation",{
        "gid":gid,"memberName":name,"type":نوع,"category":تصنيف,
        "penalty":عقوبة,"amount":غرامة,"days":أيام,
        "adminName":i.user.name,"notes":f"Discord • {i.user.name}"
    })
    color=C_RED if تصنيف=="فصل" else C_AMBER if تصنيف=="إنذار" else C_BLUE
    embed=discord.Embed(title="⚠️ مخالفة مسجلة",color=color)
    embed.add_field(name="العسكري",  value=f"**{name}** (`{gid}`)",inline=False)
    embed.add_field(name="التصنيف", value=تصنيف, inline=True)
    embed.add_field(name="المخالفة",value=نوع,   inline=True)
    embed.add_field(name="العقوبة", value=عقوبة, inline=True)
    if غرامة: embed.add_field(name="الغرامة",value=غرامة,inline=True)
    if أيام:  embed.add_field(name="الحظر",  value=f"{أيام} يوم",inline=True)
    embed.add_field(name="المسؤول",value=i.user.mention,inline=True)
    foot(embed)
    await i.followup.send(embed=embed)
    if CHANNEL_VIOLATIONS:
        ch=bot.get_channel(CHANNEL_VIOLATIONS)
        if ch and ch!=i.channel: await ch.send(embed=embed)


@tree.command(name="منح_دورة", description="منح دورة لعسكري", guild=guild_obj())
@app_commands.describe(gid="كود العسكري", دورة="c1 / c2 / c3 / c4 / c5", ملاحظة="اختياري")
async def cmd_grant(i: discord.Interaction, gid: str, دورة: str, ملاحظة: str=""):
    await i.response.defer()
    if not can_courses(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية منح الدورات"), ephemeral=True)
    gid=gid.upper().strip(); cid=دورة.strip().lower()
    if cid not in COURSE_NAMES:
        return await i.followup.send(embed=err_embed(f"الدورة يجب أن تكون: {', '.join(COURSE_NAMES.keys())}"), ephemeral=True)
    m=await get_member(gid)
    if not m: return await i.followup.send(embed=err_embed(f"العسكري **{gid}** غير موجود"))
    cd=await api_get("getCourseLog"); done=parse_courses(cd.get("data",[]),gid)
    if cid in done:
        return await i.followup.send(embed=discord.Embed(
            description=f"⚠️ العسكري أتم **{COURSE_NAMES[cid]}** مسبقاً", color=C_AMBER))
    now_ms=int(datetime.now().timestamp()*1000)
    res=await api_post("addCourseLog",{
        "id":f"cl{now_ms}","gid":gid,"name":m[1],
        "courseId":cid,"courseName":COURSE_NAMES[cid],"level":m[2],
        "adminName":i.user.name,"date":now_ms,"note":ملاحظة
    })
    if res.get("status")=="error":
        return await i.followup.send(embed=err_embed(res.get("msg","خطأ في الحفظ")))
    embed=discord.Embed(title="🎓 تم منح الدورة",color=C_GREEN)
    embed.add_field(name="العسكري", value=f"**{m[1]}** (`{gid}`)", inline=False)
    embed.add_field(name="الدورة", value=COURSE_NAMES[cid],        inline=True)
    embed.add_field(name="بواسطة",value=i.user.mention,            inline=True)
    if ملاحظة: embed.add_field(name="ملاحظة",value=ملاحظة,inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="استقالة", description="قبول استقالة عسكري", guild=guild_obj())
@app_commands.describe(gid="كود العسكري", سبب="سبب الاستقالة (اختياري)")
async def cmd_resign(i: discord.Interaction, gid: str, سبب: str=""):
    await i.response.defer()
    if not can_promote(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية"), ephemeral=True)
    gid=gid.upper().strip()
    m=await get_member(gid)
    if not m: return await i.followup.send(embed=err_embed(f"العسكري **{gid}** غير موجود"))
    discord_id = str(m[4]).strip() if m[4] and str(m[4]).strip() not in ("—","","None") else ""
    now_ms=int(datetime.now().timestamp()*1000)
    await api_post("addResigned",{
        "id":str(now_ms),"gid":gid,"name":m[1],"level":m[2],"role":m[3],
        "discord":discord_id,"type":"استقالة","reason":سبب,
        "date":now_ms,"adminName":i.user.name
    })
    await api_post("deleteMember",{"gid":gid})
    if discord_id:
        await _remove_all_level_roles(discord_id)
    embed=discord.Embed(title="📤 استقالة مقبولة",color=C_AMBER)
    embed.add_field(name="العسكري", value=f"**{m[1]}** (`{gid}`)",inline=False)
    embed.add_field(name="الرتبة", value=m[2],                    inline=True)
    embed.add_field(name="بواسطة",value=i.user.mention,           inline=True)
    if سبب: embed.add_field(name="السبب",value=سبب,inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="فصل", description="فصل عسكري من الإدارة", guild=guild_obj())
@app_commands.describe(gid="كود العسكري", سبب="سبب الفصل (مطلوب)")
async def cmd_dismiss(i: discord.Interaction, gid: str, سبب: str):
    await i.response.defer()
    if not can_promote(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية"), ephemeral=True)
    gid=gid.upper().strip()
    m=await get_member(gid)
    if not m: return await i.followup.send(embed=err_embed(f"العسكري **{gid}** غير موجود"))
    discord_id = str(m[4]).strip() if m[4] and str(m[4]).strip() not in ("—","","None") else ""
    now_ms=int(datetime.now().timestamp()*1000)
    await api_post("addResigned",{
        "id":str(now_ms+1),"gid":gid,"name":m[1],"level":m[2],"role":m[3],
        "discord":discord_id,"type":"فصل","reason":سبب,
        "date":now_ms,"adminName":i.user.name
    })
    await api_post("deleteMember",{"gid":gid})
    if discord_id:
        await _remove_all_level_roles(discord_id)
    embed=discord.Embed(title="🚫 تم الفصل",color=C_RED)
    embed.add_field(name="العسكري", value=f"**{m[1]}** (`{gid}`)",inline=False)
    embed.add_field(name="الرتبة", value=m[2],                    inline=True)
    embed.add_field(name="بواسطة",value=i.user.mention,           inline=True)
    embed.add_field(name="السبب", value=سبب,                      inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


async def _remove_all_level_roles(discord_id: str):
    if not discord_id or discord_id in ("—","","None"): return
    try:
        g = bot.get_guild(GUILD_ID)
        if not g: return
        mem = await g.fetch_member(int(discord_id))
        roles_to_remove = []
        for lvl, rid in ROLE_IDS.items():
            if rid:
                r = g.get_role(rid)
                if r and r in mem.roles:
                    roles_to_remove.append(r)
        if roles_to_remove:
            await mem.remove_roles(*roles_to_remove, reason="مغادرة إدارة الأمن العام")
            print(f"[ROLE] شالت {len(roles_to_remove)} رتبة من {mem.display_name}")
    except Exception as e:
        print(f"[REMOVE ROLES ERR] {e}")


# ══════════════════════════════════════════
#  إدارة الصلاحيات — Super Admin فقط
# ══════════════════════════════════════════

@tree.command(name="اضافة_صلاحية", description="إضافة صلاحية لعضو في البوت", guild=guild_obj())
@app_commands.describe(user_id="User ID للعضو (أرقام فقط)", perm="نوع الصلاحية")
@app_commands.choices(perm=[
    app_commands.Choice(name="كل الصلاحيات",          value="all"),
    app_commands.Choice(name="ترقية / استقالة / فصل",  value="promote"),
    app_commands.Choice(name="تسجيل مخالفات",          value="violate"),
    app_commands.Choice(name="منح دورات فقط",          value="courses"),
])
async def cmd_add_perm(i: discord.Interaction, user_id: str, perm: str):
    await i.response.defer(ephemeral=True)
    if not is_super_admin(i.user):
        return await i.followup.send(embed=err_embed("هذا الأمر للـ Super Admin فقط"), ephemeral=True)
    uid_str = user_id.strip().lstrip("<@!").rstrip(">")
    if not uid_str.isdigit():
        return await i.followup.send(embed=err_embed("أدخل User ID رقمي صحيح"), ephemeral=True)
    uid = int(uid_str)
    if uid not in BOT_PERMISSIONS: BOT_PERMISSIONS[uid] = {}
    BOT_PERMISSIONS[uid][perm] = True
    await save_permissions()
    label = PERM_LABELS.get(perm, perm)
    all_p = BOT_PERMISSIONS.get(uid, {})
    active = [PERM_LABELS.get(k,k) for k,v in all_p.items() if v]
    active_str = chr(10).join("✅ " + p for p in active)
    embed = discord.Embed(title="✅ تمت إضافة الصلاحية", color=C_GREEN)
    embed.add_field(name="العضو",     value=f"<@{uid}>",    inline=True)
    embed.add_field(name="الصلاحية", value=f"**{label}**", inline=True)
    embed.add_field(name="بواسطة",   value=i.user.mention, inline=True)
    embed.add_field(name="صلاحياته الكاملة الآن", value=active_str or "—", inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="ازالة_صلاحية", description="إزالة صلاحية من عضو", guild=guild_obj())
@app_commands.describe(user_id="User ID للعضو (أرقام فقط)", perm="نوع الصلاحية")
@app_commands.choices(perm=[
    app_commands.Choice(name="كل الصلاحيات",          value="all"),
    app_commands.Choice(name="ترقية / استقالة / فصل",  value="promote"),
    app_commands.Choice(name="تسجيل مخالفات",          value="violate"),
    app_commands.Choice(name="منح دورات فقط",          value="courses"),
    app_commands.Choice(name="إزالة كل صلاحياته",      value="__all__"),
])
async def cmd_remove_perm(i: discord.Interaction, user_id: str, perm: str):
    await i.response.defer(ephemeral=True)
    if not is_super_admin(i.user):
        return await i.followup.send(embed=err_embed("هذا الأمر للـ Super Admin فقط"), ephemeral=True)
    uid_str = user_id.strip().lstrip("<@!").rstrip(">")
    if not uid_str.isdigit():
        return await i.followup.send(embed=err_embed("أدخل User ID رقمي صحيح"), ephemeral=True)
    uid = int(uid_str)
    if perm == "__all__":
        BOT_PERMISSIONS.pop(uid, None)
        await save_permissions()
        embed = discord.Embed(title="🗑️ تمت إزالة جميع الصلاحيات", color=C_RED)
        embed.add_field(name="العضو",   value=f"<@{uid}>",   inline=True)
        embed.add_field(name="بواسطة", value=i.user.mention, inline=True)
    else:
        if uid in BOT_PERMISSIONS:
            BOT_PERMISSIONS[uid].pop(perm, None)
            if not BOT_PERMISSIONS[uid]: BOT_PERMISSIONS.pop(uid)
        await save_permissions()
        label = PERM_LABELS.get(perm, perm)
        all_p = BOT_PERMISSIONS.get(uid, {})
        active = [PERM_LABELS.get(k,k) for k,v in all_p.items() if v]
        remaining = chr(10).join("• " + p for p in active) if active else "لا توجد صلاحيات"
        embed = discord.Embed(title="🗑️ تمت إزالة الصلاحية", color=C_AMBER)
        embed.add_field(name="العضو",              value=f"<@{uid}>",    inline=True)
        embed.add_field(name="الصلاحية المُزالة", value=f"**{label}**", inline=True)
        embed.add_field(name="بواسطة",             value=i.user.mention, inline=True)
        embed.add_field(name="صلاحياته المتبقية",  value=remaining,      inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="صلاحيات", description="عرض صلاحيات عضو أو قائمة المصرح لهم", guild=guild_obj())
@app_commands.describe(user_id="User ID للعضو (اتركه فارغاً لعرض الكل)")
async def cmd_list_perms(i: discord.Interaction, user_id: str = ""):
    await i.response.defer(ephemeral=True)
    if not is_super_admin(i.user):
        return await i.followup.send(embed=err_embed("هذا الأمر للـ Super Admin فقط"), ephemeral=True)
    if user_id:
        uid_str = user_id.strip().lstrip("<@!").rstrip(">")
        if not uid_str.isdigit():
            return await i.followup.send(embed=err_embed("User ID غير صحيح"), ephemeral=True)
        uid = int(uid_str)
        perms = BOT_PERMISSIONS.get(uid, {})
        active = [PERM_LABELS.get(k,k) for k,v in perms.items() if v]
        perm_str = chr(10).join("✅ " + p for p in active) if active else "❌ لا توجد صلاحيات"
        embed = discord.Embed(title=f"🔑 صلاحيات <@{uid}>", color=C_BLUE)
        embed.add_field(name="الصلاحيات", value=perm_str, inline=False)
    else:
        embed = discord.Embed(title="🔑 قائمة المصرح لهم في البوت", color=C_BLUE)
        if BOT_PERMISSIONS:
            for uid, perms in BOT_PERMISSIONS.items():
                active = [PERM_LABELS.get(k,k) for k,v in perms.items() if v]
                if not active: continue
                perm_val = chr(10).join("• " + p for p in active)
                embed.add_field(name=f"<@{uid}>", value=perm_val, inline=True)
        else:
            embed.description = "لا يوجد أحد مضاف — فقط Super Admins"
        if SUPER_ADMIN_IDS:
            sa_list = chr(10).join(f"<@{uid}>" for uid in SUPER_ADMIN_IDS)
            embed.add_field(name="⭐ Super Admins", value=sa_list, inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


# ══════════════════════════════════════════
#  المعلومات والإحصائيات
# ══════════════════════════════════════════

@tree.command(name="احصائيات", description="إحصائيات عامة لإدارة الأمن العام", guild=guild_obj())
async def cmd_stats(i: discord.Interaction):
    await i.response.defer()
    md=await api_get("getMembers"); vd=await api_get("getViolations"); cd=await api_get("getCourseLog")
    members=md.get("data",[]); violations=vd.get("data",[]); cl=cd.get("data",[])
    active=[m for m in members if m[7]!="منصب شاغر"]
    vacant=[m for m in members if m[7]=="منصب شاغر"]
    suspended=[m for m in members if m[7]=="موقوف"]
    now=datetime.now()
    month_v=[v for v in violations if (now.timestamp()-int(v[0] or 0)/1000)<30*86400]
    completers=len({(l.get("gid","") if isinstance(l,dict) else (l[1] if len(l)>1 else "")) for l in cl if l})
    ld={}
    for m in active:
        if m[1] and m[1]!="—": ld[m[2]]=ld.get(m[2],0)+1
    embed=discord.Embed(title="📊 إحصائيات إدارة الأمن العام",color=C_PURPLE)
    embed.add_field(name="👥 عسكريون نشطون", value=str(len(active)),      inline=True)
    embed.add_field(name="🔲 مناصب شاغرة",   value=str(len(vacant)),      inline=True)
    embed.add_field(name="⏸️ موقوفون",        value=str(len(suspended)),   inline=True)
    embed.add_field(name="📦 السعة",          value=f"{len(active)}/500",  inline=True)
    embed.add_field(name="⚠️ مخالفات الشهر", value=str(len(month_v)),     inline=True)
    embed.add_field(name="📚 أتموا دورة+",    value=str(completers),       inline=True)
    top=sorted(ld.items(),key=lambda x:x[1],reverse=True)[:5]
    if top:
        top_str = "\n".join(f"{l}: **{c}** عسكري" for l,c in top)
        embed.add_field(name="📈 توزيع الرتب", value=top_str, inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="جاهزون", description="العسكريون الجاهزون للترقية", guild=guild_obj())
async def cmd_ready(i: discord.Interaction):
    await i.response.defer()
    md=await api_get("getMembers"); cd=await api_get("getCourseLog")
    members=md.get("data",[]); cl=cd.get("data",[])
    active=[m for m in members if m[7] not in ("منصب شاغر","مفصول") and m[1] and m[1]!="—"]
    ready=[]
    for m in active:
        nxt=PROMOTE_MAP.get(m[2])
        if not nxt: continue
        done=parse_courses(cl,str(m[0]).upper())
        if any(c not in done for c in REQUIRED_COURSES.get(nxt,[])): continue
        ready.append((m,nxt))
    if not ready:
        return await i.followup.send(embed=discord.Embed(description="لا يوجد عسكريون جاهزون للترقية حالياً",color=C_AMBER))
    embed=discord.Embed(title=f"🚀 جاهزون للترقية ({len(ready)})",color=C_GREEN)
    for m,nxt in ready[:10]:
        embed.add_field(name=f"`{m[0]}` — {m[1]}",value=f"{m[2]} ← **{nxt}**",inline=False)
    if len(ready)>10: embed.set_footer(text=f"يظهر أول 10 من {len(ready)} • نظام نيولوس")
    else: foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="قائمة_عسكريين", description="قائمة العسكريين حسب الرتبة (إداري)", guild=guild_obj())
@app_commands.describe(رتبة="فلتر بالرتبة — مثال: رقيب")
async def cmd_list(i: discord.Interaction, رتبة: str=""):
    await i.response.defer(ephemeral=True)
    if not can_view_admin(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية — يحتاج صلاحية إدارية"), ephemeral=True)
    d=await api_get("getMembers")
    members=[m for m in d.get("data",[]) if m[7]!="منصب شاغر" and m[1] and m[1]!="—"]
    if رتبة: members=[m for m in members if رتبة in str(m[2])]
    if not members: return await i.followup.send(embed=err_embed("لا توجد نتائج"), ephemeral=True)
    groups={}
    for m in members:
        lvl=m[2] or "—"
        if lvl not in groups: groups[lvl]=[]
        groups[lvl].append(m)
    embed=discord.Embed(title=f"🪖 قائمة العسكريين ({len(members)})",color=C_BLUE)
    for lvl,ms in list(groups.items())[:6]:
        active=[m for m in ms if m[7]=="نشط"]
        text="\n".join(f"`{m[0]}` {m[1]}" for m in active[:5])
        if len(active)>5: text+=f"\n...و {len(active)-5} آخرين"
        embed.add_field(name=f"{lvl} ({len(active)})",value=text or "—",inline=True)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="تقرير_حضور", description="تقرير حضور العسكريين (إداري)", guild=guild_obj())
async def cmd_att_report(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    if not can_view_admin(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية — يحتاج صلاحية إدارية"), ephemeral=True)
    await i.followup.send(embed=discord.Embed(description="⏳ جاري جلب بيانات الحضور...",color=C_AMBER), ephemeral=True)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(ATTENDANCE_API,timeout=aiohttp.ClientTimeout(total=20)) as r:
                att=await r.json(content_type=None)
        att_rows=att[1:] if isinstance(att,list) and len(att)>1 else []
    except: att_rows=[]
    d=await api_get("getMembers")
    members=[m for m in d.get("data",[]) if m[7]!="منصب شاغر" and m[1] and m[1]!="—"]
    results=[]
    for m in members:
        gid=str(m[0]).upper()
        rows=[r for r in att_rows if str(r[0]).strip()==gid]
        ms=0; adj=0.0; li=None
        for row in rows:
            act=str(row[3] if len(row)>3 else "").strip()
            ts=str(row[4] if len(row)>4 else "")
            if act in ("ADJUST","ADJUST_HOURS"):
                try: adj+=float(row[5] if len(row)>5 else 0)
                except: pass
                continue
            try: dt=datetime.fromisoformat(ts)
            except: dt=None
            if act=="دخول": li=dt
            elif act=="خروج" and li and dt and dt>li: ms+=(dt-li).total_seconds()*1000; li=None
        h=max(0.0,ms/3600000+adj); req=PROMO_HOURS.get(m[2])
        results.append((m,h,req))
    results.sort(key=lambda x:x[1],reverse=True)
    embed=discord.Embed(title="📊 تقرير حضور العسكريين",color=C_PURPLE)
    lines=[]
    for m,h,req in results[:15]:
        st="✅" if (req and h>=req) else "⏳" if req else "ℹ️"
        lines.append(f"{st} `{m[0]}` **{m[1]}** — {fmt_hours(h)}س {f'/{req}' if req else ''}")
    embed.description="\n".join(lines) if lines else "لا توجد بيانات"
    if len(results)>15: embed.set_footer(text=f"أول 15 من {len(results)} • نظام نيولوس")
    else: foot(embed)
    await i.edit_original_response(embed=embed)


@tree.command(name="ترقيات", description="شروط نظام الترقيات", guild=guild_obj())
@app_commands.describe(نظام="رقم النظام: 1 عسكريون / 2 معتمدون / 3 معفيون")
async def cmd_promos(i: discord.Interaction, نظام: int=1):
    await i.response.defer()
    res=await api_get("getPromos"); systems=res.get("data",[])
    if not systems:
        return await i.followup.send(embed=err_embed("لا توجد أنظمة ترقيات — أضفها من الموقع"))
    idx=max(0,min(نظام-1,len(systems)-1)); sys=systems[idx]
    embed=discord.Embed(title=f"📋 {sys.get('name','')}",color=C_GOLD)
    if sys.get("note"): embed.description=f"⚠️ {sys['note']}"
    for row in sys.get("rows",[])[:10]:
        embed.add_field(name=row.get("rank","—"),value=row.get("conditions","—"),inline=False)
    embed.set_footer(text=f"نظام نيولوس — إدارة الأمن العام • {idx+1} من {len(systems)}")
    await i.followup.send(embed=embed)


@tree.command(name="إجازات", description="رصيد الإجازات الأسبوعية", guild=guild_obj())
async def cmd_leave(i: discord.Interaction):
    await i.response.defer()
    res=await api_get("getLeave"); quota=res.get("data",{})
    if not quota:
        return await i.followup.send(embed=err_embed("لا توجد بيانات"))
    text="\n".join(f"**{lvl}**: {hrs} ساعة/أسبوع" for lvl,hrs in quota.items())
    embed=discord.Embed(title="🏖️ رصيد الإجازات الأسبوعية",description=text,color=C_GREEN)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="مركبات", description="قائمة المركبات المتاحة", guild=guild_obj())
@app_commands.describe(رتبة="فلتر بالرتبة (اختياري)")
async def cmd_vehicles(i: discord.Interaction, رتبة: str=""):
    await i.response.defer()
    res=await api_get("getVehicles"); vehicles=res.get("data",[])
    if not vehicles:
        return await i.followup.send(embed=err_embed("لا توجد مركبات"))
    if رتبة: vehicles=[v for v in vehicles if رتبة in str(v.get("level",""))]
    groups={}
    for v in vehicles:
        lvl=v.get("level","—")
        if lvl not in groups: groups[lvl]=[]
        groups[lvl].append(v)
    embed=discord.Embed(title="🚓 المركبات المتاحة",color=C_BLUE)
    for lvl,vs in groups.items():
        text="\n".join(f"{v.get('icon','🚓')} **{v.get('name','—')}** — {v.get('type','')}" for v in vs)
        embed.add_field(name=lvl,value=text,inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="مدربون", description="قائمة مدربي الورش", guild=guild_obj())
async def cmd_workshop(i: discord.Interaction):
    await i.response.defer()
    res=await api_get("getWorkshop"); raw=res.get("data",[])
    trainers=[{"gid":r[0],"name":r[1],"level":r[2],"spec":r[3],"status":r[5] if len(r)>5 else "نشط"} for r in raw]
    active=[r for r in trainers if r.get("status","نشط")=="نشط"]
    if not active: return await i.followup.send(embed=err_embed("لا يوجد مدربون"))
    embed=discord.Embed(title="🔧 مدربو الورش",color=C_BLUE)
    for r in active[:10]:
        embed.add_field(name=f"`{r.get('gid','—')}` — {r.get('name','—')}",
                        value=f"{r.get('level','—')} • {r.get('spec','—')}",inline=True)
    embed.set_footer(text=f"نظام نيولوس — إدارة الأمن العام • {len(active)} مدرب نشط")
    await i.followup.send(embed=embed)


@tree.command(name="مدراء", description="قائمة مدراء الأقسام", guild=guild_obj())
async def cmd_directors(i: discord.Interaction):
    await i.response.defer()
    res=await api_get("getDirectors"); raw=res.get("data",[])
    dirs=[{"gid":r[0],"name":r[1],"level":r[2],"dept":r[3],"role":r[5] if len(r)>5 else "—"} for r in raw]
    if not dirs: return await i.followup.send(embed=err_embed("لا يوجد مدراء"))
    embed=discord.Embed(title="🏛️ مدراء الأقسام",color=C_PURPLE)
    for r in dirs[:10]:
        embed.add_field(name=f"`{r.get('gid','—')}` — {r.get('name','—')}",
                        value=f"{r.get('level','—')} • {r.get('dept','—')} • **{r.get('role','—')}**",
                        inline=False)
    foot(embed)
    await i.followup.send(embed=embed)


@tree.command(name="مغادرون", description="سجل المستقيلين والمفصولين", guild=guild_obj())
@app_commands.describe(نوع="الكل / استقالة / فصل")
async def cmd_resigned(i: discord.Interaction, نوع: str="الكل"):
    await i.response.defer(ephemeral=True)
    if not can_view_admin(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية — يحتاج صلاحية إدارية"), ephemeral=True)
    res=await api_get("getResigned"); rows=res.get("data",[])
    if not rows: return await i.followup.send(embed=err_embed("لا توجد سجلات"))
    if نوع=="استقالة": rows=[r for r in rows if r.get("type")=="استقالة"]
    elif نوع=="فصل":   rows=[r for r in rows if r.get("type")=="فصل"]
    rows=sorted(rows,key=lambda x:x.get("date",0),reverse=True)
    tr=sum(1 for r in rows if r.get("type")=="استقالة")
    td=sum(1 for r in rows if r.get("type")=="فصل")
    embed=discord.Embed(title=f"📤 المغادرون ({len(rows)})",color=C_AMBER)
    embed.add_field(name="استقالات",value=str(tr),inline=True)
    embed.add_field(name="مفصولون", value=str(td),inline=True)
    embed.add_field(name="\u200b",  value="\u200b",inline=True)
    for r in rows[:5]:
        try: ds=datetime.fromtimestamp(r.get("date",0)/1000).strftime("%Y-%m-%d")
        except: ds="—"
        e="📤" if r.get("type")=="استقالة" else "🚫"
        embed.add_field(name=f"{e} {r.get('name','—')} ({r.get('gid','—')})",
                        value=f"{r.get('level','—')} • {r.get('reason','—')[:60]} • {ds}",inline=False)
    foot(embed)
    await i.followup.send(embed=embed, ephemeral=True)


@tree.command(name="مساعدة", description="قائمة جميع أوامر البوت", guild=guild_obj())
async def cmd_help(i: discord.Interaction):
    embed=discord.Embed(title="🤖 بوت نيولوس — إدارة الأمن العام",color=C_GOLD)
    embed.add_field(name="🪖 أوامرك الشخصية *(خاصة)*",value=(
        "`/ملفي` — ملفك الكامل\n`/ساعاتي` — ساعات حضورك\n"
        "`/مخالفاتي` — مخالفاتك\n`/دوراتي` — دوراتك"),inline=False)
    embed.add_field(name="🔍 البحث والعرض *(للجميع)*",value=(
        "`/عسكري [G-ID]`\n`/بحث [query]`\n`/حضور [G-ID]`\n"
        "`/مخالفات_عسكري [G-ID]`\n`/دورات_عسكري [G-ID]`\n`/جاهزون`\n`/احصائيات`"),inline=False)
    embed.add_field(name="⚙️ الإدارة *(يحتاج صلاحية ترقية)*",value=(
        "`/ترقية [G-ID]` — 🎭 يحدّث الرتبة + يرسل DM\n"
        "`/مخالفة [G-ID]`\n`/منح_دورة [G-ID] [c1-c5]`\n"
        "`/استقالة [G-ID]`\n`/فصل [G-ID] [سبب]`\n"
        "`/قائمة_عسكريين` *(إداري)*\n`/تقرير_حضور` *(إداري)*\n"
        "`/مغادرون` *(إداري)*\n`/تقرير`\n"
        "`/تذكير` — يرسل تذكير ساعات فوري للجميع"),inline=False)
    embed.add_field(name="🔑 الصلاحيات *(Super Admin فقط)*",value=(
        "`/اضافة_صلاحية [@عضو] [صلاحية]`\n"
        "`/ازالة_صلاحية [@عضو] [صلاحية]`\n"
        "`/صلاحيات [@عضو]`"),inline=False)
    embed.add_field(name="ℹ️ المعلومات *(للجميع)*",value=(
        "`/ترقيات [1/2/3]`\n`/إجازات`\n"
        "`/مركبات`\n`/مدربون`\n`/مدراء`"),inline=False)
    embed.set_footer(text="نظام نيولوس — إدارة الأمن العام • البيانات من Google Sheets")
    await i.response.send_message(embed=embed, ephemeral=True)


@tree.command(name="تقرير", description="إرسال تقرير يومي فوري", guild=guild_obj())
async def cmd_report(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    if not can_view_admin(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية"), ephemeral=True)
    await send_daily_report(channel_override=i.channel)
    await i.followup.send("✅ تم إرسال التقرير", ephemeral=True)


# ══════════════════════════════════════════
#  TASKS
# ══════════════════════════════════════════

@tasks.loop(hours=24)
async def daily_report(): await send_daily_report()

@daily_report.before_loop
async def before_daily():
    await bot.wait_until_ready()
    now=datetime.now()
    t=now.replace(hour=8,minute=0,second=0,microsecond=0)
    if now>=t: t+=timedelta(days=1)
    await asyncio.sleep((t-now).total_seconds())


@tasks.loop(hours=1)
async def hours_check():
    if not CHANNEL_HOURS_DONE: return
    ch=bot.get_channel(CHANNEL_HOURS_DONE)
    if not ch: return
    try:
        d=await api_get("getMembers")
        members=[m for m in d.get("data",[])
                 if m[7]!="منصب شاغر" and m[1] and m[1]!="—" and m[2] in PROMO_HOURS]
        for m in members:
            gid=str(m[0]).upper()
            key=f"{gid}_{m[2]}"
            if key in notified_hours: continue
            req=PROMO_HOURS.get(m[2],0)
            h=await calc_hours(gid)
            if h>=req:
                notified_hours.add(key)
                nxt=PROMOTE_MAP.get(m[2],"")
                disc=f"<@{m[4]}>" if m[4] and m[4]!="—" else m[1]
                embed=discord.Embed(title="✅ اكتمال ساعات الحضور",
                                    description=f"{disc} أكمل ساعات الترقية!",color=C_GREEN)
                embed.add_field(name="العسكري",       value=f"**{m[1]}** (`{gid}`)",inline=True)
                embed.add_field(name="الرتبة",        value=m[2],                   inline=True)
                embed.add_field(name="الساعات",       value=f"**{fmt_hours(h)}** / {req}س",inline=True)
                embed.add_field(name="الرتبة القادمة",value=nxt or "—",            inline=True)
                embed.set_footer(text="نظام نيولوس — إدارة الأمن العام • إشعار تلقائي")
                await ch.send(embed=embed)
                await asyncio.sleep(0.5)
    except Exception as e: print(f"[HOURS CHECK ERR] {e}")

@hours_check.before_loop
async def before_hours(): await bot.wait_until_ready()


async def send_daily_report(channel_override=None):
    ch=channel_override or (bot.get_channel(CHANNEL_REPORTS) if CHANNEL_REPORTS else None)
    if not ch: return
    try:
        md=await api_get("getMembers"); vd=await api_get("getViolations")
        members=md.get("data",[]); violations=vd.get("data",[])
        active=[m for m in members if m[7]!="منصب شاغر"]
        vacant=[m for m in members if m[7]=="منصب شاغر"]
        suspended=[m for m in members if m[7]=="موقوف"]
        now=datetime.now()
        today_v=[v for v in violations if (now.timestamp()-int(v[0] or 0)/1000)<86400]
        embed=discord.Embed(
            title="📋 التقرير اليومي — إدارة الأمن العام",
            description=f"تقرير يوم **{now.strftime('%Y-%m-%d')}**",
            color=C_GOLD, timestamp=now)
        embed.add_field(name="👥 العسكريون النشطون",value=str(len(active)),               inline=True)
        embed.add_field(name="🔲 مناصب شاغرة",      value=str(len(vacant)),               inline=True)
        embed.add_field(name="⏸️ موقوفون",           value=str(len(suspended)),            inline=True)
        embed.add_field(name="📦 نسبة الإشغال",     value=f"{int(len(active)/500*100)}%", inline=True)
        embed.add_field(name="⚠️ مخالفات اليوم",    value=str(len(today_v)),              inline=True)
        embed.add_field(name="📋 إجمالي المخالفات", value=str(len(violations)),           inline=True)
        if today_v:
            details = "\n".join(f"• **{v[2]}** (`{v[1]}`) — {v[3]}" for v in today_v[:5])
            embed.add_field(name="⚠️ تفاصيل اليوم", value=details, inline=False)
        embed.set_footer(text="نظام نيولوس — إدارة الأمن العام • تقرير تلقائي")
        await ch.send(embed=embed)
    except Exception as e:
        if ch: await ch.send(f"❌ خطأ في التقرير: {e}")


# ══════════════════════════════════════════
#  DM الترقية — رسائل عسكرية مخصصة
# ══════════════════════════════════════════

async def send_promotion_dm(
    discord_id: str, name: str,
    old_gid: str, new_gid: str,
    old_level: str, new_level: str,
    admin_name: str, note: str = ""
) -> bool:
    if not discord_id or str(discord_id).strip() in ("—", "", "None"):
        return False
    try:
        g   = bot.get_guild(GUILD_ID)
        mem = await g.fetch_member(int(discord_id))

        congrats_map = {
            "جندي أول":
                "أثبتت جديتك من اليوم الأول — هذه الرتبة بداية مسيرة طويلة، واصل! 💪",
            "عريف":
                "وصولك لرتبة العريف دليل على انضباطك والتزامك، الطريق أمامك واعد! 🌟",
            "وكيل رقيب":
                "رتبة وكيل رقيب تعكس ثقة قيادتك بك — كن عند حسن الظن! 🎯",
            "رقيب":
                "رقيب — رتبة تحمل مسؤولية ومكانة، أنت تستحق كل خطوة وصلتها! ⚡",
            "رقيب أول":
                "رقيب أول — تجاوزت النصف الأول من المسار بتميز واضح، فخر لإدارتنا! 🔥",
            "رئيس رقباء":
                "رئيس رقباء — وصلت لقمة الرتب غير الضباطية، هذا إنجاز حقيقي يُشاد به! 🏆",
            "ملازم":
                "مبروك انتقالك لسلك الضباط يا ملازم — باب جديد يفتح أمامك، أثبت جدارتك! 👮",
            "ملازم أول":
                "ملازم أول — تقدمك في سلك الضباط واضح ومحسوس، القيادة تراقبك بعين الرضا! 🌠",
            "نقيب":
                "نقيب — رتبة كبيرة تحمل مسؤوليات أكبر، أنت من الأكفاء الذين يُعتمد عليهم! 💎",
            "رائد":
                "رائد — اسم يليق بك، قائد ميداني بامتياز، الإدارة تفخر بعنصر كمثلك! 🥇",
            "مقدم ركن":
                "مقدم ركن — وصلت لرتبة القيادة العليا، ثقة الإدارة فيك لا حدود لها! ⭐",
            "عقيد ركن":
                "عقيد ركن — من أرفع الرتب في إدارتنا، أنت ركيزة أساسية لمنظومة الأمن! 🎖️",
            "عميد ركن":
                "عميد ركن — رتبة لا ينالها إلا القلة، مسيرتك نموذج يُحتذى به لكل العسكريين! 🌟",
            "لواء ركن":
                "لواء ركن — وصلت لأعلى مراتب الضباط الميدانيين، شرف عظيم وأمانة كبيرة! 👑",
        }

        congrats = congrats_map.get(
            new_level,
            f"مبروك على ترقيتك لرتبة {new_level}! تستحق كل تقدير وثناء 🎉"
        )

        next_next   = PROMOTE_MAP.get(new_level, "")
        req_courses = REQUIRED_COURSES.get(next_next, [])
        courses_txt = ""
        if next_next and req_courses:
            names = [COURSE_NAMES.get(c, c) for c in req_courses]
            courses_txt = (
                f"\n\n**📚 الدورات المطلوبة للرتبة القادمة ({next_next}):**\n"
                + "\n".join(f"• {n}" for n in names)
            )

        hours_req = PROMO_HOURS.get(new_level)
        if hours_req:
            hours_txt = f"\n**⏱️ ساعات الحضور المطلوبة للترقية القادمة:** {hours_req} ساعة"
        elif next_next:
            hours_txt = f"\n**⏱️ الترقية لـ {next_next}:** تحتاج موافقة القيادة"
        else:
            hours_txt = "\n**⭐ وصلت لأعلى الرتب — شرف عظيم!**"

        description = (
            f"## 🎊 مبروك يا {name}!\n\n"
            f"{congrats}\n\n"
            f"تمت ترقيتك رسمياً في **إدارة الأمن العام — مقاطعة نيولوس**."
        )

        embed = discord.Embed(
            title="🏅 تهنئة بالترقية العسكرية",
            description=description,
            color=C_GOLD
        )
        embed.add_field(name="🔖 الكود الجديد",    value=f"**`{new_gid}`**",             inline=True)
        embed.add_field(name="🪖 الرتبة الجديدة",  value=f"**{new_level}**",             inline=True)
        embed.add_field(name="✍️ رُقِّيت بواسطة",  value=admin_name,                     inline=True)
        embed.add_field(name="من",                  value=f"`{old_gid}` — {old_level}",   inline=True)
        embed.add_field(name="إلى",                 value=f"`{new_gid}` — **{new_level}**",inline=True)
        embed.add_field(name="\u200b",              value="\u200b",                       inline=True)

        next_steps = hours_txt + courses_txt
        if next_next:
            next_steps += f"\n\n**🎯 هدفك القادم:** {next_next}"
        else:
            next_steps += "\n\n**🌟 أنت في قمة السلم العسكري — حافظ على مكانتك!**"

        embed.add_field(name="📋 خطوتك القادمة", value=next_steps, inline=False)

        if note:
            embed.add_field(name="💬 رسالة من الإدارة", value=note, inline=False)

        embed.add_field(
            name="\u200b",
            value=(
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🫡 استمر في العطاء والتميز، الإدارة معك خطوة بخطوة."
            ),
            inline=False
        )

        embed.set_footer(text=f"نظام نيولوس — إدارة الأمن العام • {now_str()}")

        await mem.send(embed=embed)
        print(f"[PROMO DM] ✅ أُرسل لـ {name}")
        return True

    except discord.Forbidden:
        print(f"[PROMO DM] {name} أغلق DMs")
        return False
    except Exception as e:
        print(f"[PROMO DM ERR] {name}: {e}")
        return False


# ══════════════════════════════════════════
#  نظام التذكير التلقائي
# ══════════════════════════════════════════

async def send_hours_reminders(channel_override=None) -> tuple:
    d = await api_get("getMembers")
    members = [
        m for m in d.get("data", [])
        if m[7] not in ("منصب شاغر", "مفصول", "موقوف")
        and m[1] and m[1] != "—"
        and m[2] in PROMO_HOURS
        and m[4] and str(m[4]).strip() not in ("—", "", "None")
    ]

    sent = 0; completed = 0; failed = 0

    for m in members:
        gid      = str(m[0]).upper()
        req      = PROMO_HOURS.get(m[2], 0)
        hours    = await calc_hours(gid)
        nxt      = PROMOTE_MAP.get(m[2], "—")

        if hours >= req:
            completed += 1
            continue

        remaining = req - hours
        pct       = int(hours / req * 100) if req else 0
        bar       = pbar(hours, req)

        if pct >= 80:
            mood = "🔥 أنت على وشك الإنجاز، لا تتوقف الآن!"
        elif pct >= 50:
            mood = "💪 تجاوزت النصف، واصل وإنت قادر!"
        elif pct >= 25:
            mood = "⚡ بداية موفقة، الطريق أمامك!"
        else:
            mood = "🌟 الرحلة تبدأ بخطوة، ابدأ الآن!"

        embed = discord.Embed(
            title="⏰ تذكير — ساعات الحضور العسكري",
            description=(
                f"مرحباً **{m[1]}** 🫡\n\n"
                f"لاحظنا أنك لم تكمل ساعات الحضور المطلوبة للترقية بعد.\n"
                f"{mood}"
            ),
            color=C_AMBER
        )
        embed.add_field(name="كودك",             value=f"`{gid}`",                     inline=True)
        embed.add_field(name="رتبتك",            value=m[2],                           inline=True)
        embed.add_field(name="الرتبة القادمة",   value=nxt,                            inline=True)
        embed.add_field(
            name="📊 تقدمك",
            value=f"`{bar}` **{pct}%**\n{fmt_hours(hours)} من أصل {req} ساعة",
            inline=False
        )
        embed.add_field(name="⏱️ الباقي",   value=f"**{fmt_hours(remaining)}** ساعة", inline=True)
        embed.add_field(name="📅 الموعد",   value="نهاية الأسبوع",                    inline=True)
        embed.add_field(
            name="\u200b",
            value="سجّل حضورك وأثبت التزامك العسكري! 💯",
            inline=False
        )
        embed.set_footer(text="نظام نيولوس — إدارة الأمن العام • تذكير تلقائي أسبوعي")

        try:
            g   = bot.get_guild(GUILD_ID)
            mem = await g.fetch_member(int(m[4]))
            await mem.send(embed=embed)
            sent += 1
            await asyncio.sleep(0.5)
        except discord.Forbidden:
            failed += 1
            print(f"[REMINDER] {m[1]} أغلق DMs")
        except Exception as e:
            failed += 1
            print(f"[REMINDER ERR] {m[1]}: {e}")

    if channel_override:
        summary = discord.Embed(title="📨 انتهى إرسال التذكيرات", color=C_BLUE)
        summary.add_field(name="📨 أُرسل لهم",  value=str(sent),      inline=True)
        summary.add_field(name="✅ أكملوا",      value=str(completed), inline=True)
        summary.add_field(name="❌ فشل الإرسال", value=str(failed),    inline=True)
        if failed:
            summary.add_field(name="ℹ️ سبب الفشل", value="أغلق DMs أو غادر السيرفر", inline=False)
        foot(summary)
        await channel_override.send(embed=summary)

    return sent, completed, failed


@tree.command(name="تذكير", description="إرسال تذكير ساعات فوري لجميع العسكريين (إداري)", guild=guild_obj())
async def cmd_reminder(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    if not can_view_admin(i.user):
        return await i.followup.send(embed=err_embed("ليس لديك صلاحية"), ephemeral=True)
    await i.followup.send(
        embed=discord.Embed(description="⏳ جاري إرسال التذكيرات لجميع العسكريين...", color=C_AMBER),
        ephemeral=True
    )
    sent, completed, failed = await send_hours_reminders(channel_override=i.channel)
    await i.edit_original_response(
        embed=discord.Embed(
            title="✅ اكتمل الإرسال",
            description=(
                f"📨 أُرسل لهم: **{sent}**\n"
                f"✅ أكملوا ساعاتهم: **{completed}**\n"
                f"❌ فشل: **{failed}**"
            ),
            color=C_GREEN
        )
    )


@tasks.loop(hours=168)
async def weekly_reminder():
    await send_hours_reminders()

@weekly_reminder.before_loop
async def before_weekly():
    await bot.wait_until_ready()
    now = datetime.now()
    days_ahead = (3 - now.weekday()) % 7
    target = now.replace(hour=20, minute=0, second=0, microsecond=0)
    target += timedelta(days=days_ahead)
    if target <= now: target += timedelta(weeks=1)
    print(f"[REMINDER] التذكير القادم: {target.strftime('%Y-%m-%d %H:%M')}")
    await asyncio.sleep((target - now).total_seconds())


# ══════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN غير محدد في متغيرات البيئة")
    elif not GUILD_ID:
        print("❌ GUILD_ID غير محدد")
    else:
        print(f"🚀 تشغيل البوت... Guild: {GUILD_ID}")
        bot.run(BOT_TOKEN)
