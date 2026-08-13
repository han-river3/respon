import os
import threading
import time
import discord
from flask import Flask
import requests

# --- [1] Web Service용 Flask 서버 및 셀프핑 ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Selfbot is running!", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    service_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not service_url:
        return
    while True:
        time.sleep(600)
        try:
            requests.get(service_url)
        except Exception:
            pass


# --- [2] 셀프봇 클라이언트 설정 ---
# 환경변수에 봇 토큰 대신 '본인 계정 토큰(USER_TOKEN)'을 넣어야 합니다.
USER_TOKEN = os.environ.get("USER_TOKEN")
MY_USER_ID = 1533983071794233354  # 본인 계정 ID

client = discord.Client()


@client.event
async def on_ready():
    print(f"셀프봇 로그인 성공: {client.user} (ID: {client.user.id})")


@client.event
async def on_message(message: discord.Message):
    # 내가 보낸 메시지가 아니면 무시 (보안 핵심)
    if message.author.id != MY_USER_ID:
        return

    content = message.content.strip()

    # --- [기능 1] /ㄱㅈ 또는 /계좌 계좌 안내 ---
    if content in ("/ㄱㅈ", "/계좌"):
        embed = discord.Embed(
            title="🏦 입금 계좌 안내", color=discord.Color.green()
        )
        embed.add_field(name="은행", value="케이뱅크", inline=True)
        embed.add_field(name="예금주", value="ㄱㅎㅅ", inline=True)
        embed.add_field(name="계좌번호", value="`100-129-436062`", inline=False)
        embed.set_footer(text="복사하여 사용하세요.")

        try:
            await message.delete()  # 내가 쓴 /ㄱㅈ 명령어 삭제
        except Exception:
            pass

        await message.channel.send(embed=embed)
        return

    # --- [기능 2] /계산, /ㄱㅅ, /ㄳ 수수료 계산 ---
    calc_prefix = ("/계산", "/ㄱㅅ", "/ㄳ")
    if any(content.startswith(cmd) for cmd in calc_prefix):
        args = content.split()

        if len(args) < 2:
            return await message.channel.send(
                "⚠️ **사용법:** `/계산 [금액] [수수료(선택)]` (예: `/계산 10000 3.25` 또는 `/ㄱㅅ 10000`)"
            )

        try:
            amount = float(args[1].replace(",", ""))
            fee_rate_percent = (
                float(args[2].replace("%", "")) if len(args) >= 3 else 3.5
            )

            if amount <= 0 or fee_rate_percent < 0:
                raise ValueError
        except ValueError:
            return await message.channel.send(
                "⚠️ 올바른 숫자 금액과 수수료를 입력해 주세요."
            )

        fee_rate = fee_rate_percent / 100.0
        fee_amount = amount * fee_rate
        received_amount = amount - fee_amount
        required_amount = amount / (1 - fee_rate)

        embed = discord.Embed(
            title="💳 코인 수수료 계산 결과", color=discord.Color.blue()
        )
        embed.add_field(
            name="🏷️ 적용 수수료", value=f"**{fee_rate_percent}%**", inline=True
        )
        embed.add_field(
            name="💵 기준 금액", value=f"{amount:,.0f}원", inline=True
        )
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

        try:
            await message.delete()  # 내가 쓴 명령어 메시지 삭제
        except Exception:
            pass

        await message.channel.send(embed=embed)


# --- [3] 실행부 ---
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    ping_thread = threading.Thread(target=keep_alive, daemon=True)
    ping_thread.start()

    if USER_TOKEN:
        # discord.py-self 최신 버전은 bot=False 인자가 필요 없습니다.
        client.run(USER_TOKEN)
    else:
        print("에러: USER_TOKEN 환경 변수가 설정되지 않았습니다.")
