import os
import threading
import time
import discord
from flask import Flask
import requests

# --- [1] Web Service용 Flask 서버 및 셀프핑 설정 ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    """10분마다 Render 웹서비스 URL로 셀프핑 전송"""
    service_url = os.environ.get("RENDER_EXTERNAL_URL")

    if not service_url:
        print("[Self-Ping] URL 설정 없음")
        return

    print(f"[Self-Ping] 시작됨 - 대상 URL: {service_url}")
    while True:
        time.sleep(600)
        try:
            res = requests.get(service_url)
            print(f"[Self-Ping] Ping 성공! 상태 코드: {res.status_code}")
        except Exception as e:
            print(f"[Self-Ping] Ping 실패: {e}")


# --- [2] 디스코드 봇 설정 ---
TOKEN = os.environ.get("DISCORD_TOKEN")
MY_USER_ID = 1533983071794233354  # 본인 사용자 ID

intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용 읽기 권한
intents.dm_messages = True     # DM 메시지 수신 권한

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    # 봇 자신의 메시지는 무시
    if message.author == client.user:
        return

    # 본인 ID가 아니면 무시
    if message.author.id != MY_USER_ID:
        return

    # --- [기능 1] /ㄱㅈ 계좌 정보 출력 ---
    if message.content.strip() == "/ㄱㅈ":
        embed = discord.Embed(
            title="🏦 입금 계좌 안내", color=discord.Color.green()
        )
        embed.add_field(name="은행", value="케이뱅크", inline=True)
        embed.add_field(name="예금주", value="ㄱㅎㅅ", inline=True)
        embed.add_field(name="계좌번호", value="`100-129-436062`", inline=False)
        embed.set_footer(text="복사하여 사용하세요.")

        if message.guild:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

        await message.channel.send(embed=embed)
        return

    # --- [기능 2] /계산, /ㄱㅅ, /ㄳ 수수료 계산 (하나로 통합) ---
    calc_prefix = ("계산", "ㄱㅅ", "ㄳ")
    
    # 명령어 접두사 확인
    if any(message.content.startswith(f"/{cmd}") for cmd in calc_prefix):
        args = message.content.split()

        if len(args) < 2:
            return await message.channel.send(
                "⚠️ **사용법:** `/계산 [금액] [수수료(선택)]` (예: `/계산 10000 3.25` 또는 `/ㄱㅅ 10000`)"
            )

        try:
            amount = float(args[1].replace(",", ""))

            # 수수료 입력 안 하면 기본 3.5%
            if len(args) >= 3:
                fee_rate_percent = float(args[2].replace("%", ""))
            else:
                fee_rate_percent = 3.5

            if amount <= 0 or fee_rate_percent < 0:
                raise ValueError

        except ValueError:
            return await message.channel.send("⚠️ 올바른 숫자 금액과 수수료를 입력해 주세요.")

        # 수수료 계산
        fee_rate = fee_rate_percent / 100.0
        fee_amount = amount * fee_rate
        received_amount = amount - fee_amount
        required_amount = amount / (1 - fee_rate)

        # 결과 임베드
        embed = discord.Embed(
            title="💳 코인 수수료 계산 결과", color=discord.Color.blue()
        )

        embed.add_field(name="🏷️ 적용 수수료", value=f"**{fee_rate_percent}%**", inline=True)
        embed.add_field(name="💵 기준 금액", value=f"{amount:,.0f}원", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)

        embed.add_field(
            name="📥 실수령액 (입금 시)",
            value=f"• 수수료: `{fee_amount:,.0f}원`\n• 받는 금액: **`{received_amount:,.0f}원`**",
            inline=True,
        )
        embed.add_field(
            name="📤 필요 입금액 (목표 수령)",
            value=f"• 필요 금액: **`{required_amount:,.0f}원`**",
            inline=True,
        )

        embed.set_footer(text="개인 전용 수수료 계산기")

        if message.guild:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

        await message.channel.send(content=f"{message.author.mention} 님의 계산 결과:", embed=embed)


# --- [3] 실행부 ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    ping_thread = threading.Thread(target=keep_alive, daemon=True)
    ping_thread.start()

    if TOKEN:
        client.run(TOKEN)
    else:
        print("에러: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")
